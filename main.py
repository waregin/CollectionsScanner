import collections

import requests

# Press Shift+F10 to execute
input_val = input()
output_vals = ["title;author;isbn;DDC"]
while input_val != "DONE":
    # input
    google_response = requests.get("https://www.googleapis.com/books/v1/volumes?q=isbn:%s" % input_val).json()
    open_library_response = requests.get("http://openlibrary.org/api/volumes/brief/isbn/%s.json" % input_val).json()

    # output
    volume_info = google_response.get("items")[0].get("volumeInfo")
    ddc = ""
    records = open_library_response.get("records")
    for key in records:
        ddc = records[key].get("data").get("classifications").get("dewey_decimal_class")
        if isinstance(ddc, collections.abc.Sequence):
            ddc = ddc[0]
        break
    output_vals.append("%s;%s;%s;%s" % (volume_info.get("title"), volume_info.get("authors")[0], input_val, ddc))
    input_val = input()

for val in output_vals:
    print(val)