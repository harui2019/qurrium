"""
================================================================
Export data structure for qurry.expertiment.ExperimentPrototype
(:mod:`qurry.qurrium.container.export`)
================================================================

"""
from typing import Optional, NamedTuple, Any


class Export(NamedTuple):
    """Data-stored namedtuple with all experiments data which is jsonable."""

    exp_id: str = ""
    """ID of experiment, which will be packed into `.args.json`."""
    exp_name: str = "exps"
    """Name of the experiment, which will be packed into `.args.json`. 
    If this experiment is called by multimanager, 
    then this name will never apply as filename."""
    # Arguments for multi-experiment
    serial: Optional[int] = None
    """Index of experiment in a multiOutput, which will be packed into `.args.json`."""
    summoner_id: Optional[str] = None
    """ID of experiment of the multiManager, which will be packed into `.args.json`."""
    summoner_name: Optional[str] = None
    """Name of experiment of the multiManager, which will be packed into `.args.json`."""

    filename: str = ""
    """The name of file to be exported, 
    it will be decided by the :meth:`.export` when it's called.
    More info in the pydoc of :prop:`files` or :meth:`.export`, 
    which will be packed into `.args.json`.
    """
    files: dict[str, str] = {}
    """The list of file to be exported.
    For the `.write` function actually exports 4 different files
    respecting to `adventure`, `legacy`, `tales`, and `reports` like:
    
    ```python
    files = {
        'folder': './blabla_experiment/',
        'qurryinfo': './blabla_experiment/qurryinfo.json',
        
        'args': './blabla_experiment/args/blabla_experiment.id={exp_id}.args.json',
        'advent': './blabla_experiment/advent/blabla_experiment.id={exp_id}.advent.json',
        'legacy': './blabla_experiment/legacy/blabla_experiment.id={exp_id}.legacy.json',
        'tales.dummyx1': './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyx1.json',
        'tales.dummyx2': './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyx2.json',
        ...
        'tales.dummyxn': './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyxn.json',
        'reports': './blabla_experiment/reports/blabla_experiment.id={exp_id}.reports.json',
        'reports.tales.dummyz1': 
            './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyz1.reports.json',
        'reports.tales.dummyz2': 
            './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyz2.reports.json',
        ...
        'reports.tales.dummyzm': 
            './blabla_experiment/tales/blabla_experiment.id={exp_id}.dummyzm.reports.json',
    }
    ```
    which `blabla_experiment` is the example filename.
    If this experiment is called by :cls:`multimanager`, 
    then the it will be named after `summoner_name` as known as the name of :cls:`multimanager`.
    
    ```python
    files = {
        'folder': './BLABLA_project/',
        'qurryinfo': './BLABLA_project/qurryinfo.json',
        
        'args': './BLABLA_project/args/index={serial}.id={exp_id}.args.json',
        'advent': './BLABLA_project/advent/index={serial}.id={exp_id}.advent.json',
        'legacy': './BLABLA_project/legacy/index={serial}.id={exp_id}.legacy.json',
        'tales.dummyx1': './BLABLA_project/tales/index={serial}.id={exp_id}.dummyx1.json',
        'tales.dummyx2': './BLABLA_project/tales/index={serial}.id={exp_id}.dummyx2.json',
        ...
        'tales.dummyxn': './BLABLA_project/tales/index={serial}.id={exp_id}.dummyxn.json',
        'reports': './BLABLA_project/reports/index={serial}.id={exp_id}.reports.json',
        'reports.tales.dummyz1': 
            './BLABLA_project/tales/index={serial}.id={exp_id}.dummyz1.reports.json',
        'reports.tales.dummyz2': 
            './BLABLA_project/tales/index={serial}.id={exp_id}.dummyz2.reports.json',
        ...
        'reports.tales.dummyzm': 
            './BLABLA_project/tales/index={serial}.id={exp_id}.dummyzm.reports.json',
    }
    ```
    which `BLBLA_project` is the example :cls:`multimanager` name 
    stored at :prop:`commonparams.summoner_name`.
    At this senerio, the `exp_name` will never apply as filename.
    
    """

    args: dict[str, Any] = {}
    """Construct the experiment's parameters, which will be packed into `.args.json`."""
    commons: dict[str, Any] = {}
    """Construct the experiment's common parameters, which will be packed into `.args.json`."""
    outfields: dict[str, Any] = {}
    """Recording the data of other unused arguments, which will be packed into `.args.json`."""

    adventures: dict[str, Any] = {}
    """Recording the data of 'beforeward', which will be packed into `.advent.json`. 
    ~A Great Adventure begins~"""
    legacy: dict[str, Any] = {}
    """Recording the data of 'afterward', which will be packed into `.legacy.json`. 
    ~The Legacy remains from the achievement of ancestors~"""
    tales: dict[str, Any] = {}
    """Recording the data of 'side_product' in 'afterward' and 'beforewards' for API, 
    which will be packed into `.*.tales.json`. 
    ~Tales of braves circulate~"""

    reports: dict[str, dict[str, Any]] = {}
    """Recording the data of 'reports', which will be packed into `.reports.json`. 
    ~The guild concludes the results.~"""
    tales_reports: dict[str, dict[str, Any]] = {}
    """Recording the data of 'side_product' in 'reports' for API, 
    which will be packed into `.*.reprts.json`. 
    ~Tales of braves circulate~"""
