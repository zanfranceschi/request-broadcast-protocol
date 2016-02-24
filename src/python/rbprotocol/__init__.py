# -*- coding: utf-8 -*-


def checktypes(*argtypes, **kwtypes):
	def ckecktype_decorator(func):
		def func_wrapper(*args, **kwargs):
			for i in range(min(len(args) - 1, len(argtypes))):
				if (argtypes[i] is not buffer):
					# the '+ 1' is for instance or class methods -- skip self or cls
					assert args[i + 1] is None or isinstance(args[i + 1], argtypes[i]),\
						"{} should be a {} type, but is a {} type.".format(args[i + 1], argtypes[i], type(args[i + 1]))
				else:
					assert _is_buffer(args[i + 1]), "{} should support buffer interface.".format(args[i + 1])

			for k, v in kwtypes.items():
				if (v is not buffer):
					if k in kwargs:
						assert kwargs[k] is None or isinstance(kwargs[k], v),\
							"{} should be a {} type, but is a {} type.".format(k, v, type(kwargs[k]))
				else:
					assert _is_buffer(kwargs[k]), "{} should support buffer interface.".format(k)

			return func(*args, **kwargs)
		return func_wrapper
	return ckecktype_decorator


def _is_buffer(obj):
	try:
		buffer(obj)
		return True
	except TypeError:
		return False
