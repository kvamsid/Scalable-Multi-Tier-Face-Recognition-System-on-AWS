from flask import Flask, request
import pandas as pd

app = Flask(__name__)

classificationResults1000 = pd.read_csv('Classification Results on Face Dataset (1000 images).csv', index_col='Image')
classificationResults100 = pd.read_csv('Classification Results on Face Dataset (100 images).csv', index_col='Image')

@app.route("/", methods=["POST"])
def imageClassification():
    file = request.files['inputFile']
    fileName = file.filename.split('.')[0]
    if fileName in classificationResults1000.index:
        lookupTable = classificationResults1000
    elif fileName in classificationResults100.index:
        lookupTable = classificationResults100
    else:
        return "Input Image is not available"

    result = lookupTable.at[fileName, 'Results']
    return  f"{fileName}:{result}"

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, threaded=True)