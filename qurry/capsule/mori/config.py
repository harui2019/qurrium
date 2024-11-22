"""

================================================================
Configuration for multiple experiment. 
(:mod:`qurry.capsule.mori.config`)
================================================================
"""

from typing import NamedTuple, Optional, Type, Any
from collections import namedtuple
from ..jsonablize import parse as jsonablize


class DefaultConfig:
    """Default configuration for multiple experiment."""

    def __init__(
        self,
        name: str,
        default: dict[str, Any],
        default_type: Optional[dict[str, Type]] = None,
    ) -> None:
        """Set the default parameters dictionary for multiple experiment.

        A replacement of :cls:`Configuration`.

        Args:
            default (Optional[dict[Any]], optional): [description]. Defaults to None.
            name (str, optional): [description]. Defaults to 'configuration'.
        """

        self.__name__ = name
        self.__annotations__: dict[str, Type] = {}
        self.default = {}

        if default_type is None:
            default_type = {}

        for k in default.keys():
            if k in default_type:
                self.__annotations__[k] = default_type[k]
                self.default[k] = None
            else:
                self.__annotations__[k] = Type[Any]
            self.default[k] = default[k]

        self.namedtuple = namedtuple(
            field_names=self.default.keys(),
            typename=self.__name__,
            defaults=self.default.values(),
        )
        self.default_names = self.namedtuple._fields

    def __call__(self, *args, **kwargs) -> dict[str, Any]:
        return self.make(*args, **kwargs)

    def __getitem__(self, key) -> Any:
        return self.default[key]

    def __iter__(self):
        for k, v in self.default.items():
            yield k, v

    def _handle_input(
        self,
        input_object: dict[str, Any],
    ) -> None:
        """Check the input for :meth:`.check` and :meth:`.ready`.

        Args:
            inputObject (Optional[dict[Any]], optional):
                Input. Defaults to None.

        Raises:
            ValueError: When Input is None.
            TypeError: When Input is not a dict.
        """

        if not isinstance(input_object, dict):
            raise TypeError("Input must be a dict.")

    def make(
        self,
        *args: list[str],
        __values: Optional[dict[str, Any]] = None,
        partial: Optional[list[str]] = None,
        jsonable: bool = False,
    ) -> dict[str, Any]:
        """Export a dictionary of configuration.

        Args:
            __values (dict[str, Any], optional): Additonal object. Defaults to `None`
            partial (list[str], optional):
                Export parts of configuration. Defaults to `None` as exporting all.
            jsonable (bool, optional):
                Whether to make the configuration jsonable. Defaults to `False`.

        Returns:
            dict[str, Any]: A dictionary of configuration.
        """
        if len(args) > 0:
            raise ValueError(
                "Only allow one positional argument to be passed, "
                + "which is dictionary for configuration."
            )

        if __values is None:
            __values = {}
        if partial is None:
            partial = []

        config = {
            **self.default,
            **__values,
        }

        if jsonable:
            config = jsonablize(config)
        if len(partial) == 0:
            return config

        return {k: v for k, v in config.items() if k in partial}

    def as_dict(self, *args, **kwargs) -> dict[str, Any]:
        """Export configuration as a dictionary, the alternative name of :method:`make`.

        Args:
            __values (dict[str, Any]): Additonal object.
            args (list[str], optional): Positional arguments handler.
            partial (list[str], optional):
                Export parts of configuration. Defaults to `None` as exporting all.
            jsonable (bool, optional):
                Whether to make the configuration jsonable. Defaults to `False`.

        Returns:
            dict[str, Any]: A dictionary of configuration.
        """
        return self.make(*args, **kwargs)

    def as_namedtuple(
        self,
        __values: dict[str, Any],
    ) -> NamedTuple:
        """Export configuration as a namedtuple.

        Args:
            __values (dict[str, Any], optional): _description_. Defaults to {}.

        Returns:
            _type_: _description_
        """

        return self.namedtuple(**__values)

    def is_ready(
        self,
        target: dict[str, Any],
        ignores: Optional[list[str]] = None,
    ) -> bool:
        """Check whether the configuration is completed.

        Args:
            target (dict[str, Any]): The configuration want to check.
            ignores (list[str], optional): The keys to be ignored. Defaults to [].

        Returns:
            bool: Whether the configuration is completed
        """
        self._handle_input(target)
        if ignores is None:
            ignores = []
        return all(k in target or k in ignores for k in self.namedtuple._fields)

    def conclude_keys(
        self,
        target: dict[str, Any],
        excepts: Optional[list[str]] = None,
    ) -> dict[str, list[str]]:
        """Giving the list of keys include and exclude
        in the configuration from the given dictionary.

        Args:
            target (dict[str, Any]): The configuration want to check.
            excepts (list[str], optional): The exceptions. Defaults to [].

        Returns:
            dict[str, list[str]]: The contained and uncontained keys of the configuration.
        """
        self._handle_input(target)
        if excepts is None:
            excepts = []

        includes = []
        excludes = []
        for k in self.namedtuple._fields:
            if k in target or k in excepts:
                includes.append(k)
            else:
                excludes.append(k)

        return {"include": includes, "exclude": excludes}

    def exclude_keys(
        self,
        target: dict[str, Any],
        excepts: Optional[list[str]] = None,
    ) -> list[str]:
        """Giving the list of keys include in the configuration from the given dictionary.

        Args:
            target (dict[str, Any]): The configuration want to check.
            excepts (list[str], optional): The exceptions. Defaults to [].

        Returns:
            list: The uncontained keys of the configuration.
        """
        self._handle_input(target)
        if excepts is None:
            excepts = []
        return self.conclude_keys(target, excepts)["exclude"]

    def include_keys(
        self,
        target: dict[str, Any],
        excepts: Optional[list[str]] = None,
    ) -> list[str]:
        """Giving the list of keys include in the configuration from the given dictionary.

        Args:
            target (dict[str, Any]): The configuration want to check.
            excepts (list[str], optional): The exceptions. Defaults to [].

        Returns:
            list: The contained keys of the configuration.
        """
        self._handle_input(target)
        if excepts is None:
            excepts = []
        return self.conclude_keys(target, excepts)["include"]

    def useless_keys(
        self,
        target: dict[str, Any],
        ignores: Optional[list[str]] = None,
    ) -> list[str]:
        """Giving the list of keys which is useless from the given dictionary.

        Args:
            target (dict[str, Any]): The configuration want to check.
            ignores (list[str], optional): The fields to be ignored. Defaults to [].

        Returns:
            list: The contained keys of the configuration.
        """
        self._handle_input(target)
        if ignores is None:
            ignores = []

        uselesskeylist = []
        for k in target:
            if not (k in self.namedtuple._fields or k in ignores):
                uselesskeylist.append(k)

        return uselesskeylist

    def __repr__(self):
        return f"{self.namedtuple()}"
