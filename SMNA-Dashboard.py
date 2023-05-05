#!/usr/bin/env python
# coding: utf-8

# # SMNA-Dashboard
# 
# Este notebook trata da apresentação dos resultados do GSI em relação à minimização da função custo do 3DVar. A apresentação dos resultados é feita a partir da leitura de um arquivo CSV e os gráficos são mostrados em um dashboard do Panel para explorar as informações nele contidas. Para mais informações sobre o arquivo CSV e a sua estrutura de dados, veja o notebook `SMNA-Dashboard-load_files_create_dataframe_save.ipynb`.
# 
# Para realizar o deploy do dashboard no GitHub, é necessário converter este notebook em um script executável, o que pode ser feito a partir da interface do Jupyter (File -> Save and Export Notebook As... -> Executable Script). A seguir, utilize o comando abaixo para converter o script em uma página HTML. Junto com a página, será gerado um arquivo JavaScript e ambos devem ser adicionados ao repositório, junto com o arquivo CSV.
# 
# ```
# panel convert SMNA-Dashboard.py --to pyodide-worker --out .
# ```
# 
# Para utilizar o dashboard localmente, utilize o comando a seguir:
# 
# ```
# panel serve SMNA-Dashboard.ipynb --autoreload --show
# ```
# 
# ---
# Carlos Frederico Bastarz (carlos.bastarz@inpe.br), Abril de 2023.

# In[1]:


import os
import re
import numpy as np
import pandas as pd
import hvplot.pandas
import panel as pn

from datetime import datetime, timedelta
from matplotlib import pyplot as plt

pn.extension(sizing_mode="stretch_width")


# In[2]:


# Carrega o arquivo CSV

dfs = pd.read_csv('https://raw.githubusercontent.com/GAD-DIMNT-CPTEC/SMNA-Dashboard/main/jo_table_series.csv', header=[0, 1], parse_dates=[('df_dtc', 'Date'),('df_bamh_T0', 'Date'),('df_bamh_T4', 'Date'),('df_bamh_GT4AT2', 'Date'),('df_dtc_alex', 'Date')])
#dfs = pd.read_csv('jo_table_series.csv', header=[0, 1], parse_dates=[('df_dtc', 'Date'),('df_bamh_T0', 'Date'),('df_bamh_T4', 'Date'),('df_bamh_GT4AT2', 'Date'),('df_dtc_alex', 'Date')])


# In[3]:


# Separa os dataframes de interesse

df_dtc = dfs.df_dtc
df_bamh_T0 = dfs.df_bamh_T0
df_bamh_T4 = dfs.df_bamh_T4
df_bamh_GT4AT2 = dfs.df_bamh_GT4AT2
df_dtc_alex = dfs.df_dtc_alex


# In[4]:


# Atribui nomes aos dataframes

df_dtc.name = 'df_dtc'
df_bamh_T0.name = 'df_bamh_T0'
df_bamh_T4.name = 'df_bamh_T4'
df_bamh_GT4AT2.name = 'df_bamh_GT4AT2'
df_dtc_alex.name = 'df_dtc_alex'


# In[5]:


# Constrói as widgets e apresenta o dashboard

experiment_list = [df_dtc, df_bamh_T0, df_bamh_T4, df_bamh_GT4AT2, df_dtc_alex]
variable_list = ['surface pressure', 'temperature', 'wind', 'moisture', 'gps', 'radiance'] 
synoptic_time_list = ['00Z', '06Z', '12Z', '18Z', '00Z e 12Z', '06Z e 18Z']
iter_fcost_list = ['OMF', 'OMF (1st INNER LOOP)', 'OMF (2nd INNER LOOP)', 'OMA (AFTER 1st OUTER LOOP)', 'OMA (1st INNER LOOP)', 'OMA (2nd INNER LOOP)', 'OMA (AFTER 2nd OUTER LOOP)']

experiment = pn.widgets.MultiChoice(name='Experimentos', value=[experiment_list[0].name], options=[i.name for i in experiment_list], solid=False)
variable = pn.widgets.Select(name='Variável', value=variable_list[0], options=variable_list)
synoptic_time = pn.widgets.RadioBoxGroup(name='Horário', options=synoptic_time_list, inline=False)
iter_fcost = pn.widgets.Select(name='Iteração', value=iter_fcost_list[0], options=iter_fcost_list)

height=250

@pn.depends(variable, experiment, synoptic_time, iter_fcost)
def plotNobs(variable, experiment, synoptic_time, iter_fcost):
    for count, i in enumerate(experiment):
        if count == 0:
            sdf = globals()[i]
            df = dfs.xs(sdf.name, axis=1)
            
            if synoptic_time == '00Z': time_fmt0 = '00:00:00'; time_fmt1 = '00:00:00'
            if synoptic_time == '06Z': time_fmt0 = '06:00:00'; time_fmt1 = '06:00:00'
            if synoptic_time == '12Z': time_fmt0 = '12:00:00'; time_fmt1 = '12:00:00'
            if synoptic_time == '18Z': time_fmt0 = '18:00:00'; time_fmt1 = '18:00:00'    
    
            if synoptic_time == '00Z e 12Z': time_fmt0 = '00:00:00'; time_fmt1 = '12:00:00'
            if synoptic_time == '06Z e 18Z': time_fmt0 = '06:00:00'; time_fmt1 = '18:00:00'
    
            if synoptic_time == '00Z e 06Z': time_fmt0 = '00:00:00'; time_fmt1 = '06:00:00'
            if synoptic_time == '12Z e 18Z': time_fmt0 = '12:00:00'; time_fmt1 = '18:00:00'    
    
            if synoptic_time == 'Tudo': time_fmt0 = '00:00:00'; time_fmt1 = '18:00:00'   
    
            if time_fmt0 == time_fmt1:
                df_s = df.loc[df['Observation Type'] == variable].loc[df['Iter'] == iter_fcost].set_index('Date').at_time(str(time_fmt0)).reset_index()
            else:                
                df_s = df.loc[df['Observation Type'] == variable].loc[df['Iter'] == iter_fcost].set_index('Date').between_time(str(time_fmt0), str(time_fmt1), inclusive='both')
                
                if synoptic_time == '00Z e 12Z':
                    df_s = df_s.drop(df_s.at_time('06:00:00').index).reset_index()
                elif synoptic_time == '06Z e 18Z':    
                    df_s = df_s.drop(df_s.at_time('12:00:00').index).reset_index()
                
            xticks = len(df_s['Date'].values)    
                
            ax = df_s.hvplot.line(x='Date', y='Nobs', xlabel='Data', ylabel=str('Nobs'), xticks=xticks, rot=90, grid=True, label=str(i), line_width=3, height=height)
            
        else:
            
            sdf = globals()[i]
            df = dfs.xs(sdf.name, axis=1)
            
            if synoptic_time == '00Z': time_fmt0 = '00:00:00'; time_fmt1 = '00:00:00'
            if synoptic_time == '06Z': time_fmt0 = '06:00:00'; time_fmt1 = '06:00:00'
            if synoptic_time == '12Z': time_fmt0 = '12:00:00'; time_fmt1 = '12:00:00'
            if synoptic_time == '18Z': time_fmt0 = '18:00:00'; time_fmt1 = '18:00:00'    
    
            if synoptic_time == '00Z e 12Z': time_fmt0 = '00:00:00'; time_fmt1 = '12:00:00'
            if synoptic_time == '06Z e 18Z': time_fmt0 = '06:00:00'; time_fmt1 = '18:00:00'
    
            if time_fmt0 == time_fmt1:
                df_s = df.loc[df['Observation Type'] == variable].loc[df['Iter'] == iter_fcost].set_index('Date').at_time(str(time_fmt0)).reset_index()
            else:                    
                df_s = df.loc[df['Observation Type'] == variable].loc[df['Iter'] == iter_fcost].set_index('Date').between_time(str(time_fmt0), str(time_fmt1), inclusive='both')

                if synoptic_time == '00Z e 12Z':
                    df_s = df_s.drop(df_s.at_time('06:00:00').index).reset_index()
                elif synoptic_time == '06Z e 18Z':    
                    df_s = df_s.drop(df_s.at_time('12:00:00').index).reset_index()
                
            xticks = len(df_s['Date'].values)
            
            ax *= df_s.hvplot.line(x='Date', y='Nobs', xlabel='Data', ylabel=str('Nobs'), xticks=xticks, rot=90, grid=True, label=str(i), line_width=3, height=height)
            
    return ax

@pn.depends(variable, experiment, synoptic_time, iter_fcost)
def plotJo(variable, experiment, synoptic_time, iter_fcost):
    for count, i in enumerate(experiment):
        if count == 0:
            sdf = globals()[i]
            df = dfs.xs(sdf.name, axis=1)
            
            if synoptic_time == '00Z': time_fmt0 = '00:00:00'; time_fmt1 = '00:00:00'
            if synoptic_time == '06Z': time_fmt0 = '06:00:00'; time_fmt1 = '06:00:00'
            if synoptic_time == '12Z': time_fmt0 = '12:00:00'; time_fmt1 = '12:00:00'
            if synoptic_time == '18Z': time_fmt0 = '18:00:00'; time_fmt1 = '18:00:00'    
    
            if synoptic_time == '00Z e 12Z': time_fmt0 = '00:00:00'; time_fmt1 = '12:00:00'
            if synoptic_time == '06Z e 18Z': time_fmt0 = '06:00:00'; time_fmt1 = '18:00:00'
    
            if synoptic_time == '00Z e 06Z': time_fmt0 = '00:00:00'; time_fmt1 = '06:00:00'
            if synoptic_time == '12Z e 18Z': time_fmt0 = '12:00:00'; time_fmt1 = '18:00:00'    
    
            if synoptic_time == 'Tudo': time_fmt0 = '00:00:00'; time_fmt1 = '18:00:00'   
    
            if time_fmt0 == time_fmt1:
                df_s = df.loc[df['Observation Type'] == variable].loc[df['Iter'] == iter_fcost].set_index('Date').at_time(str(time_fmt0)).reset_index()
            else:                
                df_s = df.loc[df['Observation Type'] == variable].loc[df['Iter'] == iter_fcost].set_index('Date').between_time(str(time_fmt0), str(time_fmt1), inclusive='both')
                
                if synoptic_time == '00Z e 12Z':
                    df_s = df_s.drop(df_s.at_time('06:00:00').index).reset_index()
                elif synoptic_time == '06Z e 18Z':    
                    df_s = df_s.drop(df_s.at_time('12:00:00').index).reset_index()
                
            xticks = len(df_s['Date'].values)    
                
            ax = df_s.hvplot.line(x='Date', y='Jo', xlabel='Data', ylabel=str('Jo'), xticks=xticks, rot=90, grid=True, label=str(i), line_width=3, height=height)
            
        else:
            
            sdf = globals()[i]
            df = dfs.xs(sdf.name, axis=1)
            
            if synoptic_time == '00Z': time_fmt0 = '00:00:00'; time_fmt1 = '00:00:00'
            if synoptic_time == '06Z': time_fmt0 = '06:00:00'; time_fmt1 = '06:00:00'
            if synoptic_time == '12Z': time_fmt0 = '12:00:00'; time_fmt1 = '12:00:00'
            if synoptic_time == '18Z': time_fmt0 = '18:00:00'; time_fmt1 = '18:00:00'    
    
            if synoptic_time == '00Z e 12Z': time_fmt0 = '00:00:00'; time_fmt1 = '12:00:00'
            if synoptic_time == '06Z e 18Z': time_fmt0 = '06:00:00'; time_fmt1 = '18:00:00'
    
            if time_fmt0 == time_fmt1:
                df_s = df.loc[df['Observation Type'] == variable].loc[df['Iter'] == iter_fcost].set_index('Date').at_time(str(time_fmt0)).reset_index()
            else:                    
                df_s = df.loc[df['Observation Type'] == variable].loc[df['Iter'] == iter_fcost].set_index('Date').between_time(str(time_fmt0), str(time_fmt1), inclusive='both')

                if synoptic_time == '00Z e 12Z':
                    df_s = df_s.drop(df_s.at_time('06:00:00').index).reset_index()
                elif synoptic_time == '06Z e 18Z':    
                    df_s = df_s.drop(df_s.at_time('12:00:00').index).reset_index()
                
            xticks = len(df_s['Date'].values)
            
            ax *= df_s.hvplot.line(x='Date', y='Jo', xlabel='Data', ylabel=str('Jo'), xticks=xticks, rot=90, grid=True, label=str(i), line_width=3, height=height)
            
    return ax

@pn.depends(variable, experiment, synoptic_time, iter_fcost)
def plotJon(variable, experiment, synoptic_time, iter_fcost):
    for count, i in enumerate(experiment):
        if count == 0:
            sdf = globals()[i]
            df = dfs.xs(sdf.name, axis=1)
            
            if synoptic_time == '00Z': time_fmt0 = '00:00:00'; time_fmt1 = '00:00:00'
            if synoptic_time == '06Z': time_fmt0 = '06:00:00'; time_fmt1 = '06:00:00'
            if synoptic_time == '12Z': time_fmt0 = '12:00:00'; time_fmt1 = '12:00:00'
            if synoptic_time == '18Z': time_fmt0 = '18:00:00'; time_fmt1 = '18:00:00'    
    
            if synoptic_time == '00Z e 12Z': time_fmt0 = '00:00:00'; time_fmt1 = '12:00:00'
            if synoptic_time == '06Z e 18Z': time_fmt0 = '06:00:00'; time_fmt1 = '18:00:00'
    
            if synoptic_time == '00Z e 06Z': time_fmt0 = '00:00:00'; time_fmt1 = '06:00:00'
            if synoptic_time == '12Z e 18Z': time_fmt0 = '12:00:00'; time_fmt1 = '18:00:00'    
    
            if synoptic_time == 'Tudo': time_fmt0 = '00:00:00'; time_fmt1 = '18:00:00'   
    
            if time_fmt0 == time_fmt1:
                df_s = df.loc[df['Observation Type'] == variable].loc[df['Iter'] == iter_fcost].set_index('Date').at_time(str(time_fmt0)).reset_index()
            else:                
                df_s = df.loc[df['Observation Type'] == variable].loc[df['Iter'] == iter_fcost].set_index('Date').between_time(str(time_fmt0), str(time_fmt1), inclusive='both')
                
                if synoptic_time == '00Z e 12Z':
                    df_s = df_s.drop(df_s.at_time('06:00:00').index).reset_index()
                elif synoptic_time == '06Z e 18Z':    
                    df_s = df_s.drop(df_s.at_time('12:00:00').index).reset_index()
                
            xticks = len(df_s['Date'].values)    
                
            ax = df_s.hvplot.line(x='Date', y='Jo/n', xlabel='Data', ylabel=str('Jo/n'), xticks=xticks, rot=90, grid=True, label=str(i), line_width=3, height=height)
            
        else:
            
            sdf = globals()[i]
            df = dfs.xs(sdf.name, axis=1)
            
            if synoptic_time == '00Z': time_fmt0 = '00:00:00'; time_fmt1 = '00:00:00'
            if synoptic_time == '06Z': time_fmt0 = '06:00:00'; time_fmt1 = '06:00:00'
            if synoptic_time == '12Z': time_fmt0 = '12:00:00'; time_fmt1 = '12:00:00'
            if synoptic_time == '18Z': time_fmt0 = '18:00:00'; time_fmt1 = '18:00:00'    
    
            if synoptic_time == '00Z e 12Z': time_fmt0 = '00:00:00'; time_fmt1 = '12:00:00'
            if synoptic_time == '06Z e 18Z': time_fmt0 = '06:00:00'; time_fmt1 = '18:00:00'
    
            if time_fmt0 == time_fmt1:
                df_s = df.loc[df['Observation Type'] == variable].loc[df['Iter'] == iter_fcost].set_index('Date').at_time(str(time_fmt0)).reset_index()
            else:                    
                df_s = df.loc[df['Observation Type'] == variable].loc[df['Iter'] == iter_fcost].set_index('Date').between_time(str(time_fmt0), str(time_fmt1), inclusive='both')

                if synoptic_time == '00Z e 12Z':
                    df_s = df_s.drop(df_s.at_time('06:00:00').index).reset_index()
                elif synoptic_time == '06Z e 18Z':    
                    df_s = df_s.drop(df_s.at_time('12:00:00').index).reset_index()
                
            xticks = len(df_s['Date'].values)
            
            ax *= df_s.hvplot.line(x='Date', y='Jo/n', xlabel='Data', ylabel=str('Jo/n'), xticks=xticks, rot=90, grid=True, label=str(i), line_width=3, height=height)
            
    return ax

settings = pn.Row(pn.WidgetBox(variable, iter_fcost, synoptic_time, pn.Column(experiment, height=250)))
pn.Column(
    '### SMNA Dashboard', 
    settings,
    plotNobs,
    plotJo,
    plotJon,
    width_policy='max'
)

pn.template.FastListTemplate(
    site="SMNA", title="Dashboard", sidebar=[settings],
    main=[plotNobs, plotJo, plotJon]
#).show();
).servable();

# Nota: utilize o método servable() quando o script for convertido.


# In[ ]:




