

def load_model(
    name: Union[str, Path],
    *,
    vocab: Union["Vocab", bool] = True,
    disable: Union[str, Iterable[str]] = _DEFAULT_EMPTY_PIPES,
    enable: Union[str, Iterable[str]] = _DEFAULT_EMPTY_PIPES,
    exclude: Union[str, Iterable[str]] = _DEFAULT_EMPTY_PIPES,
    config: Union[Dict[str, Any], Config] = SimpleFrozenDict(),
) -> "Language":
    """Load a model from a package or data path.

    name (str): Package name or model path.
    vocab (Vocab / True): Optional vocab to pass in on initialization. If True,
        a new Vocab object will be created.
    disable (Union[str, Iterable[str]]): Name(s) of pipeline component(s) to disable.
    enable (Union[str, Iterable[str]]): Name(s) of pipeline component(s) to enable. All others will be disabled.
    exclude (Union[str, Iterable[str]]):  Name(s) of pipeline component(s) to exclude.
    config (Dict[str, Any] / Config): Config overrides as nested dict or dict
        keyed by section values in dot notation.
    RETURNS (Language): The loaded nlp object.
    """
    kwargs = {
        "vocab": vocab,
        "disable": disable,
        "enable": enable,
        "exclude": exclude,
        "config": config,
    }
    if isinstance(name, str):  # name or string path
        if name.startswith("blank:"):  # shortcut for blank model
            return get_lang_class(name.replace("blank:", ""))()
        if is_package(name):  # installed as package
            return load_model_from_package(name, **kwargs)  # type: ignore[arg-type]
        if Path(name).exists():  # path to model data directory
            return load_model_from_path(Path(name), **kwargs)  # type: ignore[arg-type]
    elif hasattr(name, "exists"):  # Path or Path-like to model data
        return load_model_from_path(name, **kwargs)  # type: ignore[arg-type]
    if name in OLD_MODEL_SHORTCUTS:
        raise IOError(Errors.E941.format(name=name, full=OLD_MODEL_SHORTCUTS[name]))  # type: ignore[index]
    raise IOError(Errors.E050.format(name=name))

