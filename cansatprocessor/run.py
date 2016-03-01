"""Contains the main code for running the application."""
from flask import Flask, request, redirect, url_for, render_template, make_response
from flask_uploads import TEXT, UploadSet, UploadNotAllowed, configure_uploads
from io import StringIO
import csv

UPLOADED_DATAFILES_DEST = "/tmp/cansatprocessor"

DEBUG = True

app = Flask(__name__)
app.config.from_object(__name__)


datafiles = UploadSet("datafiles", TEXT)
configure_uploads(app, datafiles)

HEADER_SEP = ">"
FIELD_SEP = "|"
DATA_SEP = ":"


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
    line = fh.readline().decode("ascii")
    first_line = _process_line(line)

    filebuf = StringIO()
    writer = csv.DictWriter(filebuf, list(first_line.keys()))

    writer.writeheader()
    writer.writerow(first_line)

    for line in fh:
        line = line.decode("ascii")
        try:
            row = _process_line(line)
            print(row)
            writer.writerow(row)
        except ProcessingError:
            print("Processing error.")

    return filebuf


@app.route("/", methods=["GET", "POST"])
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST" and "datafile" in request.files:
        filename = datafiles.save(request.files["datafile"])
        return redirect(url_for("return_"))
    return render_template("upload.html")


@app.route("/return", methods=["POST"])
def return_():
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
    return response


if __name__ == '__main__':
    app.run(debug=True)
