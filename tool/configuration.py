from typing import Union, Optional, Callable
from .jsonablize import Parse as jsonablize


class Configuration(dict):
    def __init__(
        self,
        default: Optional[dict[any]] = {
            "measure": "None",
            "experiment": "None",

            "qPairNum": 1,
            "qNum": 2,
            "boundaryCond": 'period',
            "alpha": 0,
            "beta": 0,

            "circuitRunBy": "operator",
            "initSet": None,
            "hamiltonianIndex": None,

            "timeEvo": range(11),
            "collectA": [[1]],

            "waveFigType": 'text',
            "waveComposeMethod": "decompose",

            "goRunby": "gate",
            "goFigType": 'text',
            "goComposeMethod": None,
            "shots": 1024,

            'singleResultKeep': False,
            'countPlotKeep': False,
            'simpleResultKeep': False,

            "expNum": None,
            "demoNum": None,
        },
        name: str = 'configuration'
    ) -> None:
        """Set the default parameters dictionary for multiple experiment.

        Args:
            default (Optional[dict[any]], optional): [description]. Defaults to None.
            name (str, optional): [description]. Defaults to 'configuration'.
        """

        self.__name__ = name
        self.default = default
        super().__init__(self.default)
        
    @classmethod
    def create(
        cls,
        default: Optional[dict[any]] = {
            "measure": "None",
            "experiment": "None",

            "qPairNum": 1,
            "qNum": 2,
            "boundaryCond": 'period',
            "alpha": 0,
            "beta": 0,

            "circuitRunBy": "operator",
            "initSet": None,
            "hamiltonianIndex": None,

            "timeEvo": range(11),
            "collectA": [[1]],

            "waveFigType": 'text',
            "waveComposeMethod": "decompose",

            "goRunby": "gate",
            "goFigType": 'text',
            "goComposeMethod": None,
            "shots": 1024,

            'singleResultKeep': False,
            'countPlotKeep': False,
            'simpleResultKeep': False,

            "expNum": None,
            "demoNum": None,
        },
        name: str = 'configuration'
    ):
        
        return cls(
            default=default,
            name=name
        )

    @staticmethod
    def paramsCollectList(
        collect: list[Union[int, list[int], dict[str, int]]]
    ) -> list[list[int]]:
        collectA = []
        for aItem in collect:
            if type(aItem) == list:
                collectA.append(aItem)
            elif type(aItem) == dict:
                collectA.append(aItem)
            elif type(aItem) == int:
                collectA.append([aItem])
            else:
                print(
                    f"Unrecognized type of input '{type(aItem)}'" +
                    " of '{aItem}' has been dropped.'")
        return collectA
    
    @staticmethod
    def paramsCollectInt(
        tgt: int
    ) -> list[list[int]]:
        return [[i] for i in range(tgt)]

    @staticmethod
    def paramsCollectRange(
        tgt: range
    ) -> list[list[int]]:
        return [[i] for i in tgt]
    
    @staticmethod
    def typeCheck(
        target: any,
        typeWantAndHandle: list[tuple[type, Union[type, Callable]]]
    ) -> Union[Exception, any]:
        """Check whether the parameter is the type which required, then  
        transform into another type or handle it with specific function.

        Args:
            target (any): The parameter
            typeWantAndHandle (list[tuple[type, Union[type, Callable]]]): 
                The required type and the 

        Raises:
            TypeError: When there is no type which meet the requirement.

        Returns:
            Union[Exception, any]: The result of handle the parameter or 
                the error which the parameter does not meet the requirement.
        """
        checkedList = []
        for typeWant, handle in typeWantAndHandle:
            checkedList.append(f'{typeWant}')
            if type(target) == typeWant:
                handle = (lambda x: x) if handle == None else handle
                return handle(target)

        raise TypeError(
            'Expected'.join([f"'{typeWant}', " for typeWant, _ in checkedList[:-1]]) +
            f"or '{checkedList[-1]}', but got '{type(target)}'. "
        )

    def make(
        self,
        inputObject: dict[any] = {},
    ) -> dict[any]:
        """[summary]

        Args:
            inputObject (dict[any], optional): [description]. Defaults to {}.

        Returns:
            dict[any]: [description]
        """
            
        configIndividual = {
            **self.default,
            **inputObject,
        }

        return configIndividual

    def jsonMake(
        self,
        inputObject: dict[any] = {},
        save: bool = False,
    ) -> dict[any]:
        """[summary]

        Args:
            inputObject (dict[any], optional): [description]. Defaults to {}.

        Returns:
            dict[any]: [description]
        """

        return jsonablize(self.make(
            inputObject=inputObject,
            save=save,
        ))

    def _handleInput(
        self,
        inputObject: Optional[dict[any]] = None
    ) -> None:
        """[summary]

        Args:
            inputObject (Optional[dict[any]], optional): 
            Input. Defaults to None.

        Raises:
            ValueError: When Input is None.
            TypeError: When Input is not a dict.
        """

        if inputObject == None:
            raise ValueError("Input can not be null.")
        elif isinstance(inputObject, dict):
            ...
        else:
            raise TypeError("Input must be a dict.")

    def check(
        self,
        target: Optional[dict[any]] = None,
    ) -> list:
        """Check whether the configuration is completed.

        Args:
            target (dict): The configuration.

        Returns:
            list: The lost keys of the configuration.
        """
        self._handleInput(target)
        return [k for k in self.default if not k in target]

    def ready(
        self,
        target: dict,
    ) -> bool:
        """Check whether the configuration is completed.

        Args:
            target (dict): The configuration

        Returns:
            bool: Whether the configuration is completed
        """
        self._handleInput(target)
        return all(k in target for k in self.default)

    def __repr__(self):
        return f"{self.__name__}({self.__dict__})"

    def jsonDefault(self):
        return jsonablize(self.__dict__)
