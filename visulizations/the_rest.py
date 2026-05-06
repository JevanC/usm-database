


    

def compare_nor_so_cal(selected_name):

        
        
        norcal_df = pd.DataFrame(norcal, columns=['Event', 'Location', 'Year', 'NorCal'])
        socal_df = pd.DataFrame(socal, columns=['Event','Location', 'Year', 'SoCal'])
        df=pd.merge(norcal_df, socal_df, on=['Event','Location', 'Year'], how='outer')

        df['Event'] = df.apply(lambda x : f"{x['Event']} {x['Location']}", axis=1)
        df['Last Year NorCal'] = ((df['NorCal'] - df['NorCal'].shift(1)) / df['NorCal'].shift(1) * 100).round(2)

        df['Last Year SoCal'] = ((df['SoCal'] - df['SoCal'].shift(1)) / df['SoCal'].shift(1) * 100).round(2)

        df['Two Year Ago NorCal'] = ((df['NorCal'] - df['NorCal'].shift(1)) / df['NorCal'].shift(2) * 100).round(2)
        df['Two Year Ago SoCal'] = ((df['SoCal'] - df['SoCal'].shift(1)) / df['SoCal'].shift(2) * 100).round(2)

        df[['Event', 'Year', 'Last Year NorCal', 'Last Year SoCal', 'Two Year Ago NorCal', 'Two Year Ago SoCal']]