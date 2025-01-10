import MetaTrader5 as mt5
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from scipy.signal import argrelextrema
import pandas as pd
import numpy as np

# Conectar ao MetaTrader 5
if not mt5.initialize():
    print("Falha ao inicializar")
    mt5.shutdown()
    exit()

# Símbolo do WING25
symbol = "WING25"

# Selecionar o símbolo
if not mt5.symbol_select(symbol, True):
    print(f"Falha ao selecionar o símbolo {symbol}")
    mt5.shutdown()
    exit()

# Obter dados históricos do gráfico de 5 minutos
rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_M5, 0, 114)

# Converter dados para um DataFrame
rates_frame = pd.DataFrame(rates)
rates_frame['time'] = pd.to_datetime(rates_frame['time'], unit='s')

# Função para calcular suportes e resistências
def calculate_support_resistance(data, window_size):
    rolling_max = data['close'].rolling(window=window_size).max()
    rolling_min = data['close'].rolling(window=window_size).min()
    
    support_levels = rolling_min.dropna().unique()
    resistance_levels = rolling_max.dropna().unique()
    
    return support_levels, resistance_levels

# Seleciona os 3 níveis mais importantes
def select_top_levels(levels, top_n=3):
    return np.sort(levels)[-top_n:]

# Função para encontrar picos locais
def find_local_maxima(data, order=5):
    indices = argrelextrema(data['close'].values, np.greater, order=order)[0]
    return data.iloc[indices]

# Função para encontrar vales locais
def find_local_minima(data, order=5):
    indices = argrelextrema(data['close'].values, np.less, order=order)[0]
    return data.iloc[indices]

# Função para atualizar o gráfico
def update(frame):
    plt.cla()
    
    # Obter o preço atual
    price = mt5.symbol_info_tick(symbol).last

    # Determinar a cor de cada segmento de linha
    colors = []
    for i in range(1, len(rates_frame)):
        if rates_frame['close'].iloc[i] >= rates_frame['close'].iloc[i-1]:
            colors.append('green')
        else:
            colors.append('red')
    
    # Plotar dados de preço com as cores determinadas e espessura aumentada
    for i in range(1, len(rates_frame)):
        plt.plot(rates_frame['time'].iloc[i-1:i+1], rates_frame['close'].iloc[i-1:i+1], color=colors[i-1], linewidth=4)

    # Calcular suportes e resistências
    window_size = 50  # Tamanho da janela para cálculo
    support_levels, resistance_levels = calculate_support_resistance(rates_frame, window_size)

    # Selecionar os 3 níveis mais importantes
    top_support_levels = select_top_levels(support_levels)
    top_resistance_levels = select_top_levels(resistance_levels)

    # Plotar suportes e resistências
    plot_support_resistance(top_support_levels, 'blue')
    plot_support_resistance(top_resistance_levels, 'red')

    # Plotar linha no preço atual
    plot_current_price_line(price)

    # Adicionar anotação com o preço atual
    plt.annotate(f'{price:.2f}', xy=(rates_frame['time'].iloc[-1], price), xytext=(10, 0), 
                 textcoords='offset points', arrowprops=dict(arrowstyle="->"), fontsize=16, color='green')

    # Adicionar as alturas de suporte e resistência à direita
    for level in top_support_levels:
        altura = (level - rates_frame['close'].min()) / (rates_frame['close'].max() - rates_frame['close'].min()) * 100
        plt.annotate(f'S: {level:.2f} ({altura:.1f}%)', xy=(rates_frame['time'].iloc[-1], level), xytext=(10, 0), 
                     textcoords='offset points', arrowprops=dict(arrowstyle="->"), fontsize=12, color='blue')
        
    for level in top_resistance_levels:
        altura = (level - rates_frame['close'].min()) / (rates_frame['close'].max() - rates_frame['close'].min()) * 100
        plt.annotate(f'R: {level:.2f} ({altura:.1f}%)', xy=(rates_frame['time'].iloc[-1], level), xytext=(10, 0), 
                     textcoords='offset points', arrowprops=dict(arrowstyle="->"), fontsize=12, color='red')

    # Encontrar picos locais para a linha de tendência de baixa
    local_maxima = find_local_maxima(rates_frame)
    if len(local_maxima) > 1:
        plt.plot(local_maxima['time'], local_maxima['close'], 'o', color='orange')  # Marcar os picos
        plt.plot(local_maxima['time'], local_maxima['close'], color='orange', linestyle='--', linewidth=2)  # Linha de tendência de baixa

    # Encontrar vales locais para a linha de tendência de alta
    local_minima = find_local_minima(rates_frame)
    if len(local_minima) > 1:
        plt.plot(local_minima['time'], local_minima['close'], 'o', color='purple')  # Marcar os vales
        plt.plot(local_minima['time'], local_minima['close'], color='purple', linestyle='--', linewidth=2)  # Linha de tendência de alta

    # Limpar dados antigos para liberar memória
    rates_frame.drop(rates_frame.index[:-100], inplace=True)

    # Ajustes finais no gráfico
    plt.title('Suportes e Resistências Dinâmicos WING25 - Gráfico 5M')
    plt.xlabel('Tempo')
    plt.ylabel('Preço')
    plt.legend()
    plt.grid(True)

# Função para plotar suportes e resistências
def plot_support_resistance(levels, color):
    for level in levels:
        plt.axhline(y=level, color=color, linestyle='-', linewidth=2)

# Função para plotar linha no preço atual
def plot_current_price_line(price):
    plt.axhline(y=price, color='green', linestyle='-', linewidth=2)

# Criar a animação
fig, ax = plt.subplots()
ani = animation.FuncAnimation(fig, update, interval=100)

# Mostrar o gráfico
plt.show()

# Desconectar do MetaTrader 5 ao terminar
mt5.shutdown()