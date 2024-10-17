import os, requests, zipfile

def download_url(url, save_path=None, chunk_size=128):
    '''    Download a file from a url   '''
    r = requests.get(url, stream=True)

    if save_path is None:
        save_path = os.path.basename(url)

    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)


def unzip(zip_path, file=None, dest='./'):
  ''' unzip a zip file
      params:
        zip_path - è il file zip da decomprimere
        file - nome di un file contenuto nello zip
               da estrarre.
               None implica l'estrazione di tutti i file
        dest - directory dove estrarre i file (default
               dir corrente)
  '''
  if zipfile.is_zipfile(zip_path):
    zfile=zipfile.ZipFile(zip_path,"r")
    if file is None:
      zfile.extractall(path=dest)
    else:
      zfile.extract(file,path=dest)
    zfile.close()

import importlib, sys, subprocess

def pip_save_requirements(packages:list):
  """
    crea file requirements.txt dalla lista di packages

    param: packages lista moduli installati
  """
  with open('requirements.txt','w+t') as fo:
    for module in packages:
      module=module if module.count('!')==0 else module.split('!')[0]
      fo.write(module+'\n')

def pip_install(packages):
  """
  per installarare pacchetti python con pip

  param: packages è una lista di moduli da installare o
         una string indicante un singolo modulo

  return numero di pacchetti installati
  """
  # param verification str or list
  if type(packages) is str:
      packages=[packages]

  ret=0
  for module in packages:
    # in caso di modili con toplevel diverso dal modulo
    # caso ipython che ha come toplevel IPython
    top_level=None
    if module.count('!')==1:
       t=module.split('!')
       module=t[0]
       top_level=t[1]

    # in caso di moduli con versione -> mudulo==1.2.3
    s=module if module.count('==')==0 else module.split('==')[0]

    s=s.replace('-','_') if top_level is None else top_level
    installed = importlib.util.find_spec(s) != None
    if installed:
      print(f'module {module} is installed')
    else:
      print(f"Installing {s} {module}")
      subprocess.call([sys.executable, '-m', 'pip', 'install','-qU', module])
      ret+=1

  return ret


if __name__ == "__main__":
  print("**",__name__,"**")

  # url download
  download_url('https://www.learningcontainer.com/wp-content/uploads/2020/05/sample-zip-file.zip',
                save_path='zip/sample.zip')

  # unzip
  # unzip('zip/sample.zip','sample.txt','zip/')
  unzip('zip/sample.zip',dest='zip/')

  ## pip_install
  lista=[
      "datasets==2.11.0",
      "dload"
  ]

  # pip_install(lista)
  # oppure...
  # pip_install('dload')
  # o
  if pip_install('dload')>0:
    pip_save_requirements(lista)