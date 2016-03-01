"""Contains the main code for running the application."""
from flask import Flask, request, render_template, make_response
from io import StringIO
import csv

DEBUG = True
HOST = "0.0.0.0"
PORT = 25564

app = Flask(__name__)
app.config.from_object(__name__)

HEADER_SEP = ">"
FIELD_SEP = "|"
DATA_SEP = ":"

ENCODING = "ascii"


class ProcessingError(Exception):
    """Error during processing of data file."""

    pass


def _process_line(line):
    result = {}

    line = line.strip()

    if line.count(HEADER_SEP) != 1:
        raise ProcessingError

    header, line = line.split(HEADER_SEP)
    result["header"] = header

    fields = line.split(FIELD_SEP)

    for field in fields:
        if DATA_SEP not in field:
            continue

        if DEBUG:
            print(field)

        key, value = field.split(DATA_SEP)

        key = key.strip()
        value = value.strip()

        result[key] = value

    return result


def transform_file(fh):
    """Transform the file to CSV format."""
    line = fh.readline().decode(ENCODING)
    first_line = _process_line(line)

    filebuf = StringIO()
    writer = csv.DictWriter(filebuf, list(first_line.keys()))

    writer.writeheader()
    writer.writerow(first_line)

    for line in fh:
        line = line.decode(ENCODING)
        try:
            row = _process_line(line)
            if DEBUG:
                print(row)
            writer.writerow(row)
        except ProcessingError:
            if DEBUG:
                print("Processing error.")

    return filebuf


@app.route("/")
@app.route("/upload")
def upload():
    """Page where users upload file."""
    return render_template("upload.html")


@app.route("/return", methods=["POST"])
def return_():
    """Returns the transformed data file."""
    file_ = request.files["datafile"]
    if not file_:
        return "No valid file! Try again"

    try:
        contents = transform_file(file_.stream).getvalue()
    except ProcessingError:
        return ("Something went wrong during processing - check the validity "
                "of your data or ask Jeppe.")
    response = make_response(contents)
    response.headers["Content-Disposition"] = "attachment; filename=data.csv"
    response.headers["Content-Type"] = "text/csv"
    return response


if __name__ == '__main__':
    app.run(debug=DEBUG, host=HOST, port=PORT)
