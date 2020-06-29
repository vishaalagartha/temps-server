def write_location_string(valid_hours):
    data = {} 
    for el in valid_hours:
        if el['date'] not in data:
            data[el['date']] = []
        data[el['date']].append(el)

    string = ''

    for d in data:
        s = f"\t Date: {d}\n"
        for h in data[d]:
            s+='\t\t'
            if h['hour']==12:
                s+=f"At 12 PM "
            elif h['hour']>12:
                s+=f"At {h['hour']-12} PM "
            else:
                s+=f"At {h['hour']} AM "
            s+=f"- {h['description']} " 
            s+=f"(Temperature: {round(h['temp']-273, 2)} °F,"
            s+=f" Humidity: {round(h['humidity'], 1)}%,"
            s+=f" Wind Speed: {round(h['wind_speed'], 1)} mph,"
            s+=f" Dewpoint: {round(h['dew_point']-273,2)} °F)"
            s+='\n'
        string+=s+'\n'

    return string
