### V2
def pulisci(codice:str,id='')->str:
  r=codice.replace('(','')
  r=r.replace(')','')
  r=r.replace('.','') # caso 16 ANOMALIA rec con . 714/.2014
  x=len(r.split('/'))

  # questo è un potenziale errore
  # if x<2:
  #   dbg.lprint(200,f'Errore codice: {id} {r}')
  return r

in_list =lambda l, x : l.index(x) if x in l else -1

def get_lex_id(text:str):
  """
  get_lex_id(text)

  dato un text contenente il testo della direttiva/regolamento ...
  cerca di dedurre il numero della legge in formato xxxxx/xxxx[/xxx]

  ritorna None se non trova corrispondenza 
  """
  val=None

  # trova preambolo
  end=text.find("\nvist")
  if (end==-1):
    end=text.find(",\nVist")

  if(end>0):
    dati=text[0:end].upper().split()

    match dati[0]:
      case 'DIRETTIVA':
        if dati[1] in ['DELEGATA','(UE)']:
          # ############################################################
          # DIRETTIVA DELAGATA AAAA/BBBB DEL PARLAMENTO
          # ############################################################
          if dati[2]=='(UE)':
            val=pulisci(dati[3],format)
          else:
            val=pulisci(dati[2],format)

        elif dati[1]=='DI' and dati[2]=='ESECUZIONE':
          # ############################################################
          # DIRETTIVA DI ESECUZIONE
          # ############################################################
          if dati[3] in ['(UE)','(EU)']:
            val=pulisci(dati[4],format)
          else:
            val=pulisci(dati[3],format)

        else:
          val=pulisci(dati[1],format)

      case 'DECISIONE':
        if dati[1] in ['(UE)','N.']:
          # ############################################################
          # DECISIONE (UE) 2015/41 [DEL PARLAMENTO | DELLA COMMISSIONE]
          # ############################################################
          val=dati[2]
          if val=='N.':
            val=pulisci(dati[3],format)

        elif dati[1]=='DEL' and dati[2]=='CONSIGLIO':
          # ############################################################
          # DECISIONE DEL CONSIGLIO del 23...
          # ############################################################
          val=pulisci(dati[-5],format)

        elif dati[2]=='DEL' and dati[3]=='CONSIGLIO':
          # ############################################################
          # DECISIONE 2013/306/PESC DEL CONSIGLIO
          # ############################################################
          val=pulisci(dati[1],format)

        elif dati[1]=='DI' and dati[2]=='ESECUZIONE':
          # ############################################################
          # DECISIONE DI ESECUZIONE
          # ############################################################
          if dati[3] in ['(UE)','(EU)']:
            val=pulisci(dati[4],format)
          elif dati[4]=='CONSIGLIO':
            val=pulisci(dati[-5],format)
          elif dati[4]=='DEL':
            val=pulisci(dati[3],format)
          else:
            val=pulisci(dati[-4],format)

        elif dati[1]=='DELLA' and dati[2]=='COMMISSIONE' and dati[-1]=='EUROPEA,':
          # ############################################################
          # DECISIONE DELLA COMMISSIONE ...  (2013/131/UE) LA COMMISSIONE EUROPEA,
          # ############################################################
          val=pulisci(dati[-4],format)

        elif dati[1]=='(PESC)':
          # ############################################################
          # DECISIONE (PESC) 2015/260
          # ############################################################
          val=pulisci(dati[2],format)

        elif (pos:=text.find("DEL COMITATO POLITICO"))!=-1:
          # ############################################################
          # DECISIONE DEL COMITATO POLITICO
          # ############################################################
          dati=text[0:pos].split()
          val=pulisci(dati[-1],format)

        elif (pos:=text.find("IL PARLAMENTO EUROPEO E IL CONSIGLIO DELL"))!=-1:
          dati=text[0:pos].split()
          val=pulisci(dati[-1],format)
        else:
          # dbg.lprint(100,format,dati)
          pass # None

      case 'REGOLAMENTO':
        n=in_list(dati,'N.')

        if n!=-1:
          val=pulisci(dati[n+1])

        elif (n:=in_list(dati,'(UE)'))!=-1:
          val=pulisci(dati[n+1])

        else:
          # dbg.lprint(101,dati)
          pass # None
  else:
    # print(f'Errore no \ n rec:{r.Index}', r.text[:500])
    pass

  return val
