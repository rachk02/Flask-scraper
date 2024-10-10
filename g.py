import plotly.graph_objects as go

fig = go.Figure(data=[go.Bar(y=[2, 3, 1])])
fig.show()  # Cela ouvrira une fenêtre de navigateur au lieu de sauvegarder en tant qu'image.
