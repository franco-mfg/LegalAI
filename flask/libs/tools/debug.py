import sys

class Debug:
  """
    implementation classe for simple debug

    usage: dbg=Debug(False|True [default])

    dbg.print(data...)

    if parameter is False then nothing is printed
  """
  def __init__(self,debug=True) -> None:
    # print('Debug:','ON' if debug else 'OFF')
    self.__DEBUG__=debug

  def on(self):
    """
    True debug is enabled

    usage:
    dbg=Debug(True)

    if dbg.on():
      operation_if_on

    """
    return self.__DEBUG__==True

  def print(self,*args):
    """
    usare al posto di print(...)
    stampa alcun messaggio.
    """
    # print('Debug:','ON' if self.__DEBUG__ else 'OFF')

    if not self.__DEBUG__:
      return None

    res=''
    for i in args:
      res+=f' {i}'

    print(res, file=sys.stderr)
