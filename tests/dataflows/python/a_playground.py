@classmethod
def _from_pretrained(
    cls,
    resolved_vocab_files,
    pretrained_model_name_or_path,
    init_configuration,
    *init_inputs,
    token=None,
    cache_dir=None,
    local_files_only=False,
    _commit_hash=None,
    _is_local=False,
    **kwargs,
):
    # We instantiate fast tokenizers based on a slow tokenizer if we don't have access to the tokenizer.json
    # file or if `from_slow` is set to True.


    # Prepare tokenizer initialization kwargs
    # Did we saved some inputs and kwargs to reload ?
    tokenizer_config_file = resolved_vocab_files.pop("tokenizer_config_file", None)
    if tokenizer_config_file is not None:
        with open(tokenizer_config_file, encoding="utf-8") as tokenizer_config_handle:
            init_kwargs = json.load(tokenizer_config_handle)
        # First attempt. We get tokenizer_class from tokenizer_config to check mismatch between tokenizers.
        config_tokenizer_class = init_kwargs.get("tokenizer_class")
        init_kwargs.pop("tokenizer_class", None)
        if not has_tokenizer_file:
            init_kwargs.pop("tokenizer_file", None)
        saved_init_inputs = init_kwargs.pop("init_inputs", ())
        if not init_inputs:
            init_inputs = saved_init_inputs
    else:
        config_tokenizer_class = None
        init_kwargs = init_configuration

    if "auto_map" in init_kwargs and not _is_local:
        # For backward compatibility with odl format.
        if isinstance(init_kwargs["auto_map"], (tuple, list)):
            init_kwargs["auto_map"] = {"AutoTokenizer": init_kwargs["auto_map"]}
        init_kwargs["auto_map"] = add_model_info_to_auto_map(
            init_kwargs["auto_map"], pretrained_model_name_or_path
        )



    # Update with newly provided kwargs
    init_kwargs.update(kwargs)

    # Set max length if needed
    if pretrained_model_name_or_path in cls.max_model_input_sizes:
        # if we're using a pretrained model, ensure the tokenizer
        # wont index sequences longer than the number of positional embeddings

        model_max_length = cls.max_model_input_sizes[pretrained_model_name_or_path]
        if model_max_length is not None and isinstance(model_max_length, (int, float)):
            model_max_length = min(init_kwargs.get("model_max_length", int(1e30)), model_max_length)
            # TODO(PVP) - uncomment following line in Transformers v5
            # init_kwargs["model_max_length"] = model_max_length
            # TODO(PVP) - remove in Transformers v5
            # ---
            init_kwargs["model_max_length"] = cls._eventually_correct_t5_max_length(
                pretrained_model_name_or_path, model_max_length, init_kwargs.get("model_max_length")
            )
            # ---

    # Merge resolved_vocab_files arguments in init_kwargs.
    added_tokens_file = resolved_vocab_files.pop("added_tokens_file", None)
    special_tokens_map_file = resolved_vocab_files.pop("special_tokens_map_file", None)
    for args_name, file_path in resolved_vocab_files.items():
        if args_name not in init_kwargs:
            init_kwargs[args_name] = file_path
    tokenizer_file = resolved_vocab_files.pop("tokenizer_file", None)

    if slow_tokenizer is not None:
        init_kwargs["__slow_tokenizer"] = slow_tokenizer
    init_kwargs["name_or_path"] = pretrained_model_name_or_path

    #### Handle tokenizer serialization of added and special tokens
    added_tokens_decoder: Dict[int, AddedToken] = {}
    added_tokens_map: Dict[str, AddedToken] = {}
    # if we have info on the slow added tokens
    if "added_tokens_decoder" in init_kwargs:
        for idx, token in init_kwargs["added_tokens_decoder"].items():
            if isinstance(token, dict):
                token = AddedToken(**token)
            if isinstance(token, AddedToken):
                added_tokens_decoder[int(idx)] = token
                added_tokens_map[str(token)] = token
            else:
                raise ValueError(
                    f"Found a {token.__class__} in the saved `added_tokens_decoder`, should be a dictionary or an AddedToken instance"
                )
    else:
        # begin legacy: read the added_tokens_file and update kwargs with special_tokens_map if modified
        if special_tokens_map_file is not None:
            with open(special_tokens_map_file, encoding="utf-8") as special_tokens_map_handle:
                special_tokens_map = json.load(special_tokens_map_handle)
                for key, value in special_tokens_map.items():
                    if key in kwargs and kwargs[key]:
                        # This value has already been redefined by the kwargs
                        # We keep this new value and ignore the one stored in the special_tokens_map_file
                        continue
                    if isinstance(value, dict):
                        value = AddedToken(**value, special=True)
                    elif key == "additional_special_tokens" and isinstance(value, list):
                        additional_special_tokens = init_kwargs.pop("additional_special_tokens", []) or []
                        for token in value:
                            token = AddedToken(**token, special=True) if isinstance(token, dict) else token
                            if token not in additional_special_tokens:
                                additional_special_tokens.append(token)
                        value = additional_special_tokens
                    init_kwargs[key] = value

        # slow -> slow|fast, legacy: convert the `"added_tokens.json"` file to `added_tokens_decoder`.
        # this is for legacy purpose. We don't add the tokens after init for efficiency.
        if added_tokens_file is not None:
            special_tokens = []
            for key in cls.SPECIAL_TOKENS_ATTRIBUTES & init_kwargs.keys():
                if init_kwargs[key] is not None:
                    if key == "additional_special_tokens":
                        special_tokens += [str(token) for token in init_kwargs[key]]
                    else:
                        special_tokens.append(str(init_kwargs[key]))

            with open(added_tokens_file, encoding="utf-8") as added_tokens_handle:
                added_tok_encoder = json.load(added_tokens_handle)
            for str_token, index in added_tok_encoder.items():
                # if index not in added_tokens_decoder and str_token not in added_tokens_map:
                special = str_token in special_tokens
                added_tokens_decoder[index] = AddedToken(
                    str_token, rstrip=False, lstrip=False, normalized=not special, special=special
                )
                added_tokens_map[str(token)] = added_tokens_decoder[index]

        # allows converting a fast -> slow: add the `tokenizer.json`'s `"added_tokens"` to the slow tokenizer
        # if `tokenizer_config.json` is `None`


    # Passing AddedTokens and not strings to the class to prevent it from casting the string to a different AddedToken
    for key in init_kwargs.keys():
        if added_tokens_map != {} and init_kwargs[key] is not None:
            if key != "additional_special_tokens":
                init_kwargs[key] = added_tokens_map.get(init_kwargs[key], init_kwargs[key])

    init_kwargs["added_tokens_decoder"] = added_tokens_decoder
    # convert {'__type': 'AddedToken', 'content': '<ent>', 'lstrip': False, 'normalized': True, ...} to AddedTokens
    init_kwargs = cls.convert_added_tokens(init_kwargs, save=False)
    # Instantiate the tokenizer.
    try:
        tokenizer = cls(*init_inputs, **init_kwargs)
    except OSError:
        raise OSError(
            "Unable to load vocabulary from file. "
            "Please check that the provided vocabulary is accessible and not corrupted."
        )

    if added_tokens_decoder != {} and max(list(added_tokens_decoder.keys())[-1], 0) > tokenizer.vocab_size:
        logger.warning_advice(
            "Special tokens have been added in the vocabulary, make sure the associated word embeddings are"
            " fine-tuned or trained."
        )
    return tokenizer
_from_pretrained()
