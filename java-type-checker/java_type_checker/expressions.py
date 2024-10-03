# -*- coding: utf-8 -*-

from .types import JavaBuiltInTypes, JavaTypeError


class JavaExpression(object):
    """AST for simple Java expressions.

    Note that this library deals only with compile-time types, and this class therefore does not
    actually *evaluate* expressions.
    """

    def static_type(self):
        """Returns the compile-time type of this expression as a JavaType.

        Subclasses must override this method.
        """
        raise NotImplementedError(type(self).__name__ + " must override static_type()")

    def check_types(self):
        """Examines the structure of this expression for static type errors.

        Raises a JavaTypeError if there is an error. If there is no error, this method has no effect
        and returns nothing.

        Subclasses must override this method.
        """
        raise NotImplementedError(type(self).__name__ + " must override check_types()")


class JavaVariable(JavaExpression):
    """An expression that reads the value of a variable, e.g. `x` in the expression `x + 5`.

    In a real Java language implementation, the declared_type would be filled in by a name resolver
    after the initial construction of the AST. In this sample project, however, we simply specify
    the declared_type for every variable reference.
    """
    def __init__(self, name, declared_type):
        self.name = name                    #: The name of the variable (str)
        self.declared_type = declared_type  #: The declared type of the variable (JavaType)
    def static_type(self):
        return self.declared_type
    def check_types(self):
        pass



class JavaLiteral(JavaExpression):
    """A literal value entered in the code, e.g. `5` in the expression `x + 5`.
    """
    def __init__(self, value, type):
        self.value = value  #: The literal value, as a string
        self.type = type    #: The type of the literal (JavaType)
    def static_type(self):
        return self.type 

    def check_types(self):
        pass



class JavaNullLiteral(JavaLiteral):
    """The literal value `null` in Java code.
    """
    def __init__(self):
        super().__init__("null", JavaBuiltInTypes.NULL)
    def static_type(self):
        return JavaBuiltInTypes.NULL


class JavaAssignment(JavaExpression):
    """The assignment of a new value to a variable.

    Attributes:
        lhs (JavaVariable): The variable whose value this assignment updates.
        rhs (JavaExpression): The expression whose value will be assigned to the lhs.
    """
    def __init__(self, lhs, rhs):
        self.lhs = lhs
        self.rhs = rhs
    def static_type(self):
        return self.lhs.declared_type
    def check_types(self):
    # Ensure lhs and rhs types are compatible
        self.lhs.check_types()
        self.rhs.check_types()
        
        lhs_type = self.lhs.static_type()
        rhs_type = self.rhs.static_type()

        if not rhs_type.is_subtype_of(lhs_type):
            raise JavaTypeMismatchError(
            f"Cannot assign {rhs_type.name} to variable {self.lhs.name} of type {lhs_type.name}"
        )

class JavaMethodCall(JavaExpression):
    """A Java method invocation.

    For example, in this Java code::

        foo.bar(0, 1)

    - The receiver is `JavaVariable(foo, JavaObjectType(...))`
    - The method_name is `"bar"`
    - The args are `[JavaLiteral("0", JavaBuiltInTypes.INT), ...etc...]`

    Attributes:
        receiver (JavaExpression): The object whose method we are calling
        method_name (String): The name of the method to call
        args (list of Expressions): The arguments to pass to the method
    """
    def __init__(self, receiver, method_name, *args):
        self.receiver = receiver
        self.method_name = method_name
        self.args = args
    def static_type(self):
        receiver_type = self.receiver.static_type()  # Get the static type of the receiver
        # Assuming we have a method to look up the method return type by receiver type and method name
        method_return_type = receiver_type.method_named(self.method_name)
        return method_return_type

    def check_types(self):
    # Check the types of the receiver and the arguments
        self.receiver.check_types()  # Ensure the receiver is valid

        # Get the expected method from the receiver's type
        receiver_type = self.receiver.static_type()
        method = receiver_type.method_named(self.method_name)

        # Check if the method exists
        if method is None:
            raise JavaTypeError(
                f"Method '{self.method_name}' not found on type '{receiver_type.name}'."
            )

        # # Check the number of arguments
        expected_params = method.parameter_types # Get expected parameter types
        # print(len(expected_params))
        # print(len(self.args))
        # print("Method Name:", self.method_name)
        # print("Expected parameter types:", expected_params)  # Ensure this is being set correctly
        # print("Actual argument count:", len(self.args))
        if len(self.args) != len(expected_params):
            raise JavaArgumentCountError(
                f"Method {self.method_name} expects {len(expected_params)} arguments but got {len(self.args)}."
            )

        # # Check each argument type
        # for arg, expected_param in zip(self.args, expected_params):
        #     # arg.check_types()  # Ensure the argument itself is valid
        #     arg_type = arg.static_type()

        #     if not arg_type.is_subtype_of(expected_param):
        #         raise JavaTypeMismatchError(
        #             f"Cannot pass argument of type {arg_type.name} to parameter of type {expected_param.name}."
        #         )
   
    


class JavaConstructorCall(JavaExpression):
    """
    A Java object instantiation

    For example, in this Java code::

        new Foo(0, 1, 2)

    - The instantiated_type is `JavaObjectType("Foo", ...)`
    - The args are `[JavaLiteral("0", JavaBuiltInTypes.INT), ...etc...]`

    Attributes:
        instantiated_type (JavaType): The type to instantiate
        args (list of Expressions): Constructor arguments
    """
    def __init__(self, instantiated_type, *args):
        self.instantiated_type = instantiated_type
        self.args = args

    def static_type(self):
        return self.instantiated_type

class JavaTypeMismatchError(JavaTypeError):
    """Indicates that one or more expressions do not evaluate to the correct type.
    """
    pass


class JavaArgumentCountError(JavaTypeError):
    """Indicates that a call to a method or constructor has the wrong number of arguments.
    """
    pass


class JavaIllegalInstantiationError(JavaTypeError):
    """Raised in response to `new Foo()` where `Foo` is not an instantiable type.
    """
    pass


def _names(named_things):
    """Helper for formatting pretty error messages
    """
    return "(" + ", ".join([e.name for e in named_things]) + ")"
