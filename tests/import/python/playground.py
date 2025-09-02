def mock_context(
    mock_services: InvocationServices,
) :
    return build_invocation_context(
        services=mock_services,
        data=None,  # type: ignore
        is_canceled=None,  # type: ignore
    )
