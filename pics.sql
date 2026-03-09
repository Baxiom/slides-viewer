
CREATE DATABASE pics;
USE pets

#One record for each image file
CREATE TABLE files
(
  id              INT unsigned NOT NULL AUTO_INCREMENT, # Unique ID for the record
  drive           VARCHAR(50) NOT NULL,                 # The name of the drive the file is on
  filename        VARCHAR(150) NOT NULL,                # Full path string of file
  location        VARCHAR(150),                         # Full geo location string
  taken           DATETIME NOT NULL,                    # Date and time that the image was taken
  PRIMARY KEY     (id)                                  # Make the id the primary key
);
