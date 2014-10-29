from collections import OrderedDict
from distutils.version import StrictVersion

from babelapi.data_type import Empty

class Api(object):
    """
    A full description of an API's namespaces, data types, and routes.
    """
    def __init__(self, version):
        self.version = StrictVersion(version)
        self.namespaces = OrderedDict()

    def ensure_namespace(self, name):
        """
        Only creates a namespace if it hasn't yet been defined.

        :param str name: Name of the namespace.

        :return ApiNamespace:
        """
        if name not in self.namespaces:
            self.namespaces[name] = ApiNamespace(name)
        return self.namespaces.get(name)

class ApiNamespace(object):
    """
    Represents a category of API endpoints and their associated data types.
    """

    def __init__(self, name):
        self.name = name
        self.routes = []
        self.route_by_name = {}
        self.data_types = []
        self.data_type_by_name = {}

    def add_route(self, route):
        self.routes.append(route)
        self.route_by_name[route.name] = route

    def add_data_type(self, data_type):
        self.data_types.append(data_type)
        self.data_type_by_name[data_type.name] = data_type

    def linearize_data_types(self):
        """
        Returns a list of all data types used in the namespace. Because the
        inheritance of data types can be modeled as a DAG, the list will be a
        linearization of the DAG. It's ideal to generate data types in this
        order so that composite types that reference other composite types are
        defined in the correct order.
        """
        linearized_data_types = []
        seen_data_types = set()

        found_empty = False
        for route in self.routes:
            for segment in (route.request_segmentation.segments
                                + route.response_segmentation.segments):
                if segment.data_type == Empty and not found_empty:
                    linearized_data_types.append(Empty)
                    seen_data_types.add(Empty)
                    found_empty = True
                    break

        def add_data_type(data_type):
            if data_type in seen_data_types:
                return
            if data_type.super_type:
                add_data_type(data_type.super_type)
            linearized_data_types.append(data_type)
            seen_data_types.add(data_type)

        for data_type in self.data_types:
            add_data_type(data_type)

        return linearized_data_types

class ApiRoute(object):
    """
    Represents an API endpoint.
    """

    def __init__(self,
                 name,
                 path,
                 doc,
                 request_segmentation,
                 response_segmentation,
                 error_data_type,
                 extras):
        """
        :param str name: Friendly name of the endpoint.
        :param str path: Request path.
        :param str doc: Description of the endpoint.
        :param Segmentation request_segmentation: The segmentation of the
            request.
        :param Segmentation segmentation: The segmentation of the response.
        :param DataType error_data_type: The data type that represents
            possible errors.
        """

        self.name = name
        self.path = path
        self.doc = doc
        self.request_segmentation = request_segmentation
        self.response_segmentation = response_segmentation
        self.error_data_type = error_data_type
        self.extras = extras