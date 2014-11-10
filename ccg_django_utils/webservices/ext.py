from django.conf.urls.defaults import patterns, url
from django.core.exceptions import FieldError
from ccg import introspect
from django.db import transaction
from django.http import HttpResponse, HttpResponseBadRequest, HttpResponseNotAllowed, HttpResponseNotFound, HttpResponseServerError
from django.utils.encoding import smart_str
from json import dumps, loads


class ExtJsonInterface(object):
    """
    A mixin that can be dropped into a ModelAdmin to provide a Web service
    which implements the semantics of the ExtJS JsonStore, JsonReader and
    JsonWriter objects, provided they're constructed with the restful option on
    and the encode option off.

    Note that this needs to be defined in the class inheritance list before
    ModelAdmin to ensure methods are called in the correct order.

    The records that can be manipulated through this interface can be
    restricted by defining the queryset() function on the ModelAdmin, since the
    result of that function is used as the basis for any further filtering and
    manipulation.
    """

    CONTENT_TYPE = "application/json; charset=UTF-8"

    def serialise(self, records):
        """
        The default serialiser: given an iterable of records, this function
        returns a JSON encoded array including the metadata that ExtJS expects
        to set the relevant field types.

        Internally, this calls serialise_fields, which may be defined on a
        model to return the ExtJS data types for each field.
        """
        
        def django_type_to_ext_type(field):
            """
            Given a Django type, converts it to one of the types defined by
            ExtJS.
            """

            # Obviously this isn't terribly comprehensive: string types can go
            # through as "auto", and field types beyond the standard set in
            # Django 1.2 aren't going to be handled gracefully. Still, it's a
            # start.
            MAPPING = {
                "AutoField": "int",
                "BigIntegerField": "int",
                "BooleanField": "boolean",
                "DateField": "date",
                "DateTimeField": "date",
                "FloatField": "float",
                "IntegerField": "int",
                "NullBooleanField": "boolean",
                "PositiveIntegerField": "int",
                "PositiveSmallIntegerField": "int",
                "SmallIntegerField": "int",
                "TimeField": "date",
            }

            if field.foreign_key:
                return django_type_to_ext_type(introspect.Model(field.to).primary_key)

            if field.type in MAPPING:
                return MAPPING[field.type]

            return "auto"

        rows = []
        for record in records:
            rows.append(self.serialise_record(record))

        def serialise_fields(model):
            """
            Default field metadata generator. Given a model, this will return
            an array of field definitions that can be given to ExtJS within the
            metadata element.

            This can be overridden on a model by model basis by defining a
            serialised_fields() method on that model.
            """

            fields = []

            for field in introspect.Model(model).fields.itervalues():
                fields.append({
                    "name": field.name,
                    "type": django_type_to_ext_type(field),
                })

                if field.foreign_key:
                    fields.append({
                        "name": field.name + "__unicode",
                        "type": "string",
                    })

            return fields

        try:
            if callable(self.model.serialised_fields):
                fields = self.model.serialised_fields()
            else:
                fields = serialise_fields(self.model)
        except AttributeError:
            fields = serialise_fields(self.model)

        metadata = {
            "root": "rows",
            "idProperty": introspect.Model(self.model).primary_key.name,
            "successProperty": "success",
            "fields": fields
        }

        obj = {
            "metaData": metadata,
            "rows": rows,
        }

        return dumps(obj, indent=4, ensure_ascii=False)


    def serialise_record(self, record):
        """
        Takes a record and turns it into a dict representing the fields on that
        record. By default, this calls an inner function to do this in a
        standard way; models can override this by defining a serialise()
        method.

        Generally, this function shouldn't need to be called directly, since
        serialise() will call this as appropriate.
        """

        def serialise_record(record):
            d = {}

            for name, field in introspect.Model(record).fields.iteritems():
                # It's helpful to return both the primary key and string
                # representation of foreign keys.
                value = getattr(record, name)

                if field.foreign_key:
                    # The value might actually be None if it's nullable.
                    try:
                        d[name] = value.pk
                        d[name + "__unicode"] = unicode(value)
                    except AttributeError:
                        d[name] = None
                        d[name + "__unicode"] = u""
                elif field.many_to_many:
                    d[name] = [v.pk for v in value.all()]
                else:
                    # No foreign key relationship.
                    
                    # convert to the python type
                    d[name] = field.pythontype(value)

            return d

        serialiser = serialise_record
        try:
            if callable(self.model.serialise):
                serialiser = lambda record: record.serialise()
        except AttributeError:
            pass

        return serialiser(record)


    def set_field(self, instance, field, value):
        """
        Set a field on an instance of the ModelAdmin's model while
        respecting foreign keys. Surely there's an easier way to do this in
        Django, but I'll be damned if I can figure out how.
        """

        field = introspect.Model(self.model).fields[field]
        if field.many_to_many:
            # The value should be a list of primary keys. Hopefully.
            objects = [field.to.objects.get(pk=pk) for pk in value]

            # Remove existing many-to-many values, since update operations
            # always replace the entire set.
            getattr(instance, field.name).clear()
            getattr(instance, field.name).add(*objects)

            return
        elif field.foreign_key:
            actual = field.to.objects.get(pk=value)
        else:
            actual = value

        setattr(instance, field.name, actual)


    @transaction.commit_manually
    def handle_create(self, request):
        """
        Request handler for create requests. This will handle POST requests of
        both JSON and URL encoded data.
        """

        o = self.model()
        i = introspect.Model(self.model)
        
        # Pull in the JSON data that's been sent, if it is in fact JSON.
        try:
            row = loads(request.raw_post_data)["data"]
        except ValueError:
            # If it's not JSON, then it's probably URL encoded, and if it's
            # not, we're not going to know how to deal with it anyway.
            row = request.POST

        try:
            # Many to many fields have to be handled last, after the record has
            # been saved and a primary key has been generated. 
            m2m = []

            for field in row:
                if i.fields[field].many_to_many:
                    m2m.append(field)
                else:
                    self.set_field(o, field, row[field])

            if len(m2m) > 0:
                o.save()
                for field in m2m:
                    self.set_field(o, field, row[field])
        except Exception, e:
            transaction.rollback()

            response = {
                "success": False,
                "message": "Unable to parse incoming record.",
            }

            response['exception']=str(traceback.format_exc())
            
            return HttpResponseBadRequest(content_type=self.CONTENT_TYPE, content=dumps(response))

        o.save()
        transaction.commit()

        response = {
            "success": True,
            "message": "Created new record.",
            "data": self.serialise_record(o),
        }

        return HttpResponse(content_type=self.CONTENT_TYPE, content=dumps(response))


    @transaction.commit_on_success
    def handle_delete(self, request, id):
        """
        Request handler for delete requests.
        """

        try:
            o = self.queryset(request).get(pk=id)
            o.delete()

            response = {
                "success": True,
                "message": "Record deleted.",
            }

            return HttpResponse(content_type=self.CONTENT_TYPE, content=dumps(response))
        except self.model.DoesNotExist:
            response = {
                "success": False,
                "message": "The record could not be found.",
            }
            
            return HttpResponseNotFound(content_type=self.CONTENT_TYPE, content=dumps(response))


    def handle_read(self, request):
        """
        Request handler for read requests. This supports arbitrary filters
        which will be given to the queryset filter() function as keyword
        arguments, and also sort and dir GET parameters, which will be used to
        influence sorting. This allows the remoteSort parameter to be turned on
        within the ExtJS JsonStore object.

        This function will ignore a GET parameter called _dc to be compatible
        with Prototype, which may be used via an adapter within ExtJS. Other
        invalid filters will result in 400 responses.
        """

        qs = self.queryset(request)

        # Add filters.
        filters = {}
        for field, term in request.GET.iteritems():
            if field not in ("sort", "dir", "_dc"):
                filters[smart_str(field)] = term

        if len(filters) > 0:
            try:
                qs = qs.filter(**filters)
            except FieldError:
                # Bad parameter to QuerySet.filter.
                return HttpResponseBadRequest(content_type=self.CONTENT_TYPE, content=dumps("Bad search term"))

        # Apply sorting parameters, if given.
        if "sort" in request.GET and "dir" in request.GET:
            field = request.GET["sort"]
            if request.GET["dir"].lower() == "desc":
                field = "-" + field
            qs = qs.order_by(field)

        return HttpResponse(content_type=self.CONTENT_TYPE, content=self.serialise(qs))


    @transaction.commit_manually
    def handle_update(self, request, id):
        """
        Request handler for update requests. This function only supports JSON
        request bodies.

        Updates take place within a single transaction, so updates are
        guaranteed to be atomic -- if an error is returned, then the update is
        guaranteed not to have succeeded.
        """

        try:
            # Grab the name of the primary key field.
            pk = introspect.Model(self.model).primary_key.name

            # Pull in the JSON data that's been sent.
            row = loads(request.raw_post_data)["data"]
            qs = self.queryset(request)

            # OK, retrieve the object and update the field(s).
            o = qs.get(pk=id)
            for name, value in row.iteritems():
                self.set_field(o, name, value)
            o.save()

            # If we've gotten here, all is well.
            transaction.commit()

            response = {
                "success": True,
                "data": self.serialise_record(o),
            }

            return HttpResponse(content_type=self.CONTENT_TYPE, content=dumps(response))
        except self.model.DoesNotExist:
            transaction.rollback()

            response = {
                "success": False,
                "message": "The record could not be found.",
            }
            
            return HttpResponseNotFound(content_type=self.CONTENT_TYPE, content=dumps(response))
        except ValueError:
            transaction.rollback()

            response = {
                "success": False,
                "message": "Unable to parse incoming record.",
            }

            return HttpResponseBadRequest(content_type=self.CONTENT_TYPE, content=dumps(response))
        except Exception:
            transaction.rollback()

            response = {
                "success": False,
                "message": "An internal error occurred.",
            }
            
            return HttpResponseServerError(content_type=self.CONTENT_TYPE, content=dumps(response))

    
    def get_urls(self):
        """
        Override for ModelAdmin.get_urls() to add the appropriate URL routing
        for the Web service calls.
        """

        urls = super(ExtJsonInterface, self).get_urls()
        local_urls = patterns("",
            url(r"^ext/json/{0,1}$", self.admin_site.admin_view(self.root_dispatcher)),
            url(r"^ext/json/(?P<id>[0-9]+)$", self.admin_site.admin_view(self.id_dispatcher)),
        )

        return local_urls + urls


    def id_dispatcher(self, request, id):
        """
        Dispatcher for requests that include a record ID, which in ExtJS land
        mean requests to update or delete a record via the PUT and DELETE
        methods, respectively.
        """

        if request.method == "PUT":
            return self.handle_update(request, id)
        elif request.method == "DELETE":
            return self.handle_delete(request, id)
        else:
            return HttpResponseNotAllowed(["PUT", "DELETE"])


    def root_dispatcher(self, request):
        """
        Dispatcher for requests that don't include a record ID. These may be
        read or create requests via the GET and POST methods, respectively.
        """

        if request.method == "GET":
            return self.handle_read(request)
        elif request.method == "POST":
            return self.handle_create(request)
        else:
            # Unknown method.
            return HttpResponseNotAllowed(["GET", "POST"])
