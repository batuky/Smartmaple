# Web Scraper

Python script that performs web scraping of the first 50 pages of `https://turkishnetworktimes.com/kategori/gundem/` website's news every 20 mins until you stop it (using Ctrl+C in the Windows terminal).

## Features

- Web Scraping
    - Data retrieval from the specified news site for URL, header, summary, text, img_url_list, publish_date, and update_date columns.
    - Using requests and beautifulsoup libraries for simultaneous data retrieval.
    - Structuring the retrieved data for MongoDB.
- Data Analysis
    - Analyzing the retrieved data focusing on the text column.
    - Determining and counting the most used words in the text column.
- Word Frequency Graph
    - Generating a graph (bar chart) showing the counts of the most used words in the text column.
- MongoDB Integration
    - Creating functions/classes for simultaneous connections to MongoDB using pymongo.
    - Creating a database for URL, header, summary, text, img_url_list, publish_date, and update_date columns.
- Log Management
    - Adding logging functionality to log events, errors, and information during data retrieval, analysis, and database operations.
    - Recording important events, exceptions, and critical information for monitoring and debugging purposes.
- Data Manipulation
    - Displaying data grouped by the update_date column.
- Threading Control
    - Integrating the threadingpool library into the data retrieval, analysis, and database interaction processes.
    - Managing concurrent tasks with Python's threadingpool library, ensuring synchronization and thread safety.
- Scalability and Efficiency
    - Providing data on data retrieval speed, the amount of retrieved data, the date of data retrieval, and the number of successful/failed requests made during data retrieval.
    - Storing this efficiency data in a newly opened MongoDB collection.


## Installation

-Provide an environment variable for `mongo_uri`.

-You can build and run it with Docker.

## Optional Function Usage
On the console, a question will be displayed for the user to answer within 10 seconds. If an input is provided, the program will execute based on that input and print the output to the console. If no input is provided within 10 seconds, the program will continue running with the default value.

## License

MIT

**Free Software**

