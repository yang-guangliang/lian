class ImagePromptTemplate(BasePromptTemplate[ImageURL]):
    def __init__(self, **kwargs: Any) -> None:
        if "input_variables" not in kwargs:
            kwargs["input_variables"] = []

        overlap = set(kwargs["input_variables"]) & {"url", "path", "detail"}
        if overlap:
            msg = (
                "input_variables for the image template cannot contain"
                " any of 'url', 'path', or 'detail'."
                f" Found: {overlap}"
            )
            raise ValueError(msg)
        super().__init__(**kwargs)

ImagePromptTemplate()
