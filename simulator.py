#!/usr/bin/env python
# coding: utf-8


from statsmodels.tsa.seasonal import STL
from scipy.stats import boxcox
import seaborn
import matplotlib.pyplot as plt
import itertools
import numpy as np
from scipy.special import inv_boxcox



def ts_simulator(df, ts_column, simulations=20, periodicity='monthly'):
    if periodicity=='monthly':
        period=12
    elif periodicity=='weekly':
        period=52
    elif periodicty=='daily':
        period=365
    
    outputDF = pd.DataFrame(index=df.index)
    
    for s in range(simulations):
    
        # Perform Box-Cox Transformation
        bc_transform = boxcox(df[ts_column])
        # Store lambda
        lam = bc_transform[1]
        # Store the Box-Cox transformed dataframe with the date index
        bc_df = pd.DataFrame(bc_transform[0],
                             index=df.index,
                             columns=["BC_TRANSFORMED"])
    
        # Perform Loess decomposition
        decomp = STL(bc_df["BC_TRANSFORMED"],
                 period=period,
                 robust=False).fit()
    
    
        # Perform a block bootstrap on the residuals
        e=[ele for ele in list(range(int(len(decomp.resid)/24))) for i in range(24)]
    
        # Match the length of the randomized blocks with the original dataset length
        if len(e) > len(decomp.resid):
            e = e[:len(decomp.resid)]
        else:
            e = e + list(itertools.repeat(e[-1], (len(decomp.resid) - len(e))))
        
        # Store the residuals dataframe with the reference column
        resid = pd.DataFrame({"refVal": e,
                              "resid": decomp.resid})
        #resid["Date"] = resid.index
        resid.set_index("refVal", inplace=True)
    
        # Sample the reference column to randomize the blocks
        sampled = np.random.choice(resid.index.unique(), 
                               size=resid.index.unique().size, 
                               replace=False)
        resid = resid.loc[sampled]
        resid["refVal"] = resid.index
        resid = resid.reset_index(drop=True)
    
    
        # Create a dataframe from the seasonal and trend components
        newDF = pd.DataFrame({"ST": decomp.trend + decomp.seasonal})
        newDF["Date"] = newDF.index
        newDF = newDF.reset_index(drop=True) # Necessary to join with the randomized residuals

        # Join the S&T dataframe with the residuals
        newDF = pd.concat([newDF, resid], axis=1)
        
        # Perform an inverse Box-Cox Transformation on the simulated values with the stored lambda value
        newDF[ts_column] = inv_boxcox(newDF["ST"]+newDF["resid"], lam)
        newDF = newDF.set_index("Date")

        # Store as a new column in the Output Dataframe
        outputDF = pd.concat([outputDF, newDF[ts_column]], axis=1)
    
    return outputDF




import pandas as pd

rpm = pd.read_csv("C:/Users/deram/Downloads/RPM.csv",
                 index_col="DATE")
rpm.index = pd.to_datetime(rpm.index)


sims = ts_simulator(df=rpm, ts_column="RPM")

for c in range(len(sims.columns)):
    plt.plot(sims.iloc[:,c]);
plt.title("Bootstraped Time Series, Revenue Passenger Miles\n")
