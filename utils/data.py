from datetime import datetime, timedelta,date 

def obter_ultimos_dias():
    data_atual = date.today()- timedelta(days=1)
    
    
    lista_dias = [
        (data_atual - timedelta(days=i)).strftime('%d/%m/%Y') 
        for i in range(1)  
    ]
    
    # Inverte a lista para que fique na ordem cronológica (do mais antigo ao mais recente)
    lista_dias.reverse()
    
    print(f"MEUS ULTIMOS 15 DIAS: {lista_dias[0]} até {lista_dias[-1]}")
    return lista_dias

