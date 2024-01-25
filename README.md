Simple app to accept input of ISBNs and use two API calls to find
information about the book. This information is then output as
semicolon separated values to be pasted into my Collections database.

In the future, I would like this application to also work for other collections of mine.

Perhaps making different barcodes for values indicating which collection I am adding to using
https://barcode.tec-it.com/en

Possible list:
- PRINT_BOOKS
- FILM
- VIDEO_GAMES
- BOARD_GAMES
- PUZZLES
- PLUSHIES
- DONE (to indicate nothing more to scan at the time)

APIs being used / considered:
- Google Books APIs https://developers.google.com/books/docs/v1/using
- Open Library API https://openlibrary.org/dev/docs/api/read
- Amazon Product Advertising API https://webservices.amazon.com/paapi5/documentation/use-cases/search-with-external-identifiers.html
- Book Databases Overview https://bookscouter.com/blog/book-databases/