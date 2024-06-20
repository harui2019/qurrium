# from typing import Literal

# from .qurstrop import StringOperatorV3 as StringOperatorOrigin


# def StringOperator(
#     *args,
#     method: Literal['original'] = 'original',
#     **kwargs,
# ) -> StringOperatorOrigin:
#     """Call `StringOperator` methods.

#     Args:
#         method (Literal[&#39;original&#39;], optional):

#             - original: the original `StringOperator`.
#             Defaults to 'original'.

#     Returns:
#         StringOperatorOrigin: method.
#     """
#     if method == 'original':
#         return StringOperatorOrigin(*args, **kwargs)
#     else:
#         return StringOperatorOrigin(*args, **kwargs)
