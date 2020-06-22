"""
Created on Thu Jan  2 15:59:19 2020

@author: pedri
"""
#dashboard version 8: importing new stuff to show real data 

import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
import time
import plotly.graph_objects as go
import dash_table
import pandas as pd 
import pandas_datareader.data as web 
import numpy as np
import yahoo_fin.stock_info as si
import yfinance as yf
import FinanceToolpack as fin
import plotly.express as px


#############  Input  ###############


#Enter the tickers for the companies held in the portfolio:
securities=['SBUX','NEE','TSLA','ADBE','GOOGL','REI']

#Enter the number of shares bought in each company:
nShares=[5,6,3,7,9,20]

#Enter the amount of cash reserves, if any:
cash=0

#Enter the date of the investment in the format 'yyyy-mm-dd':
investmentDate='2018-1-1'



######################################
#__________________________________________________________________________________________________

#Data Preparation:


port= fin.createPortfolio(securities, start=investmentDate)
hist=fin.portHistPerformance(port, nShares=nShares)
indivRtns= fin.portIndivRtns(port)

sp500= web.DataReader('^GSPC', 'yahoo', start=investmentDate)['Adj Close']
sp500.dropna(0, inplace=True)

hist['SP500']=sp500.values
hist=fin.normalize(hist)

totInvested=np.sum((port.iloc[-1]*nShares).values)
latestVals=port.iloc[-1].values*nShares
wghts=np.array([i/totInvested for i in latestVals])


#test data for table and pie chart
d={'Securities':port.columns.values,
   'Shares':nShares,
   'Weight(%)':[round(j*100, 3) for j in wghts],
   'Return(%)':[round(v*100, 2) for v in indivRtns.values],
   }
df=pd.DataFrame(d)

####################
tots=df.sum(axis=0)
tots[0]='Total'





#pie charts - do it in a callback in the future 

labels = port.columns.tolist()
values = [round(j*100, 3) for j in wghts]
dta=[go.Pie(labels=labels, values=values)]


groups=['Energy','Utilities','Technology','Consumer Discretionary','Consumer Cyclical']
val=[0.1,19.9,45,5,30]
dta2=[go.Pie(labels=groups, values=val)]



# Portfolio Statistics
totRtn=(hist.iloc[-1,0]-hist.iloc[0,0])/hist.iloc[0,0]
totRsk=fin.portExpectedVolatility(port, wghts)
bta= fin.getPortBeta(port, wghts)
shrp= fin.portSharpe(port, wghts)
divYld=fin.portDivYield(port, nShares=nShares)
totAsst=totInvested
reb=investmentDate


tots[-1]=totRtn*100
df=df.append(tots,ignore_index=True)


index=['Total Return(%)',
        'Standard Deviation(%)',
        'Beta (5y daily)',
        'Sharpe Ratio',
        'Dividend Yield(%)',
        'Position Value',
        'Cash Reserve',
        'Total Asset Value',
        'Last Rebalance',
       ]
values=[round(totRtn*100, 3),
        round(totRsk*100, 3),
        round(bta,3),
        round(shrp,3),
        round(divYld*100,3),
        round(totAsst,3),
        cash,
        round(totAsst+cash,2),
        reb]
stats=pd.DataFrame(index=index)
stats['Statistic']=index
stats['Value']=values


#Correlation Heatmap

corMx=fin.getCorrMatrix(port)
dta3=[go.Heatmap(z=corMx.values,
                  x=securities,
                  y=securities,
                  hoverongaps = False)]
      
      

#_________________________________________________________________________________________________________________
######## DASH ##########

#CSS Boostraps
external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css']

#create a dash object
app = dash.Dash(__name__,external_stylesheets=external_stylesheets)

app.title='NJIT Inv Fund Portfolio'

#Add some color

colors = {'background': '#000066','text': '#cc0000'}


clrs=['#000099','#990000','#663300','#660066','#f0f0f5']

#main layout
app.layout = html.Div(   
    html.Div([
        html.Div([
            html.Div([
                html.H1(
                    children='NJIT Investment Fund Portfolio',
                    style={
                        'margin-left':20,
                        'color': '#ffffff'
                    }
                ),
        
                html.Div(
                    children='''Last Refresh: '''+time.asctime(),
                    style={
                        'margin-left':20,
                        'color': colors['text']
                    }
                         
                ),
            
            ],className='eight columns'),
            html.Div([
                html.Img(
                    src='https://s3.amazonaws.com/utep-uploads/wp-content/uploads/NJIT/2018/08/25125155/NJIT_Red_Logo_WEB.png',
                    style={
                        'height':'60%',
                        'width':'60%',
                        'float':'right',
                        'position':'relative',
                        'margin-right':50,
                        'margin-top':20
                    }
                )
            ],className='four columns')
        ],
        style={
            'backgroundColor': colors['background'],
            
            
        },
        className='row'),

        html.Div([
            html.Div([
                dcc.Graph(
                    id='pie_chart',
                    figure={
                        'data': dta,
                        'layout': {
                            'title': 'Portfolio Distribution'
                        } 
                    }
                )
            ],className='six columns'),
            
            html.Div([
                html.H5([
                    'Holdings and Returns'
                ],
                style={
                    'textAlign': 'center'
                }
                ),
                dash_table.DataTable(
                    id='holdings_table',
                    columns=[{"name": i, "id": i} for i in df.columns],
                    data=df.to_dict('records'),
                    style_cell={'textAlign': 'left'},
                    style_data_conditional=[
                        
                        {
                            'if': {'row_index': 'odd'},
                            'backgroundColor': 'rgb(248, 248, 248)'
                        },
                        #--------------------
                        {
                            'if': {
                                'column_id': 'Return(%)',
                                'filter_query': '{Return(%)} < 0'
                            },
                            'backgroundColor': 'rgb(255,0,0)',
                            'color': 'white',
                        },
                        {
                            'if': {
                                'column_id': 'Return(%)',
                                'filter_query': '{Return(%)} < -5'
                            },
                            'backgroundColor': 'rgb(153,0,0)',
                            'color': 'white',
                        },
                        {
                            'if': {
                                'column_id': 'Return(%)',
                                'filter_query': '{Return(%)} >0'
                            },
                            'backgroundColor': 'rgb(255,204, 0)',
                            'color': 'white',
                        },
                        {
                            'if': {
                                'column_id': 'Return(%)',
                                'filter_query': '{Return(%)} >8'
                            },
                            'backgroundColor': 'rgb(51,204, 51)',
                            'color': 'white',
                        }
                        #--------------------
                    ],
                    style_header={
                        'backgroundColor': 'rgb(230, 230, 230)',
                        'fontWeight': 'bold'
                    }    
                )
                
            ],
            style={
                'margin-left':20,
                'margin-top':40
            },
            className='six columns')
            
        ],className='row'),                
        html.Div([
            dcc.Graph(
                id='main_chart',
                figure={
                    'data': [
                        {'x': hist.index, 'y': hist['Historical Performance'].values, 'type': 'line', 'name': 'Portfolio'},
                        {'x':hist.index, 'y':hist['SP500'].values, 'type': 'line', 'name': 'S&P 500'},
                    ],
                    'layout': {
                        'title': 'Portfolio vs. S&P 500',
                        'xaxis' : dict(
                            title='Date',
                            titlefont=dict(
                            family='Helvetica, monospace',
                            size=20,
                            color='#7f7f7f'
                        )),
                        'yaxis' : dict(
                            title='Price (normalized to 100)',
                            titlefont=dict(
                            family='Helvetica, monospace',
                            size=20,
                            color='#7f7f7f'
                        ))
                    }
                }
            )  
        ],className='row'),
        html.Div([
            html.Div([
            html.H5([
                    'Portfolio Statistics'
                ],
                style={
                    'textAlign': 'left'
                }
                ),
                dash_table.DataTable(
                    id='stats_table',
                    columns=[{"name": i, "id": i} for i in stats.columns],
                    data=stats.to_dict('records'),
                    style_cell={'textAlign': 'left'},
                    style_as_list_view=True,
                    style_header={
                        'backgroundColor': 'white',
                        'fontWeight': 'bold'
                        }
                    )
            ], className='four columns'),
        html.Div([
            dcc.Graph(
                    id='pie_chart2',
                    figure={
                        'data': dta2,
                        'layout': {
                            'title': 'Sector Breakdown'
                        } 
                    }
                )
            ],className='four columns'),
        html.Div([
            dcc.Graph(
                    id='heatmap',
                    figure={
                        'data': dta3,
                        'layout': {
                            'title': ' Portfolio\'s Assets Correlation'
                        } 
                    }
                )
            ],className='four columns')
        ], className='row'),
        html.Div([
            html.H4(['Our Work :'
                ]),
            html.P(['The NJIT Investment Fund is long-only and student-managed, with focus on equity research and the application of \
                    value investing concepts into building a portfolio. The group of studends perform their on reseach using technology provided by the \
                     NJIT\'s Martin Tuchman School of Management and the kind contribution of Mr. Raymond Cassetta. The research\
                    and investment have an educational purpose, and must not be seen as a form of profit for the participating \
                    students. The fund is open to all interested NJIT students across all majors.'
                ]),
            html.H6([
                'Executive Board \
                - Daniel Encarnacao: de59@njit.edu \
                - Marina Arrese: ma2323@njit.edu \
                - Pedro D\'Avila : pd372@njit.edu \
                - Logan Heft: lbh3@njit.edu'
                ])
            ], className='row'),
        html.Div([
            html.Div([
                html.Img(
                    src='https://media-exp1.licdn.com/dms/image/C4E03AQHU7W6RRVb6Zw/profile-displayphoto-shrink_800_800/0?e=1597881600&v=beta&t=cWdhLaAEat8sB-1c8uD8UmPjaOivV7PNgNC78Es4f_A',
                    style={
                        'height':'60%',
                        'width':'60%',
                        'float':'right',
                        'position':'relative',
                        'margin-right':50,
                        'margin-top':20
                    }
                )
                ], className='three columns'),
            html.Div([
                html.Img(
                    src='https://media-exp1.licdn.com/dms/image/C4D03AQEvJaNS4f1uPA/profile-displayphoto-shrink_800_800/0?e=1597881600&v=beta&t=XYsDE_leyamatzgZ5OgcaSj0cRQoU_vzXuVtQ7tPE3c',
                    style={
                        'height':'60%',
                        'width':'60%',
                        'float':'right',
                        'position':'relative',
                        'margin-right':50,
                        'margin-top':20
                    }
                )
                ], className='three columns'),
            html.Div([
                html.Img(
                    src='https://media-exp1.licdn.com/dms/image/C4E03AQGrZkXLHOt4Cw/profile-displayphoto-shrink_800_800/0?e=1597881600&v=beta&t=OtDtu6eCABVIJeZJpTss38l_IVR2a388-efYF3iNUaM',
                    style={
                        'height':'60%',
                        'width':'60%',
                        'float':'right',
                        'position':'relative',
                        'margin-right':50,
                        'margin-top':20
                    }
                )
                ], className='three columns'),
            html.Div([
                html.Img(
                    src='https://media-exp1.licdn.com/dms/image/C4E03AQHCFUJhfB3oRw/profile-displayphoto-shrink_800_800/0?e=1597881600&v=beta&t=gHcpbemaztqxfbet04dqpn4vKGcfs5E-IGSMpin9VQc',
                    style={
                        'height':'60%',
                        'width':'60%',
                        'float':'right',
                        'position':'relative',
                        'margin-right':50,
                        'margin-top':20
                    }
                )
                ], className='three columns')
            
            ], className='row'),
        html.Div([
            html.P([
                'Credits: Dashboard coded in python by Pedro D\'Avila'
                ], className='four columns'),
            html.Div([
                html.Img(
                    src='https://businessanalyticslabnjit.files.wordpress.com/2017/10/cropped-njit_logo2.jpg?w=1400',
                    style={
                        'height':'75%',
                        'width':'120%',
                        'float':'right',
                        'position':'relative',
                        'margin-right':20,
                        'margin-top':50,
                        'margin-left':20
                    }
                )
                ], className='four columns')
            ], className='row')
        
    ])
)
                    

#run the app            
if __name__ == '__main__':
    app.run_server(debug=True)
