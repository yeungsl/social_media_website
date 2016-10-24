CREATE DATABASE photoshare;
USE photoshare;
DROP TABLE Pictures CASCADE;
DROP TABLE Users CASCADE;
DROP TABLE Friends CASCADE;
DROP TABLE Albums CASCADE;
DROP TABLE Pictures CASCADE;
DROP TABLE Tags CASCADE;
DROP TABLE Comments CASCADE;

CREATE TABLE Users (
  `user_id` int(11) NOT NULL AUTO_INCREMENT,
  `first_name` varchar(255) NOT NULL,
  `last_name` varchar(255) NOT NULL,
  `date_of_birth` date NOT NULL,
  `email` varchar(255) NOT NULL,
  `hometown` varchar(255) NOT NULL,
  `gender` enum('male', 'female') NOT NULL,
  `password` varchar(255) NOT NULL,
  CONSTRAINT userid_pk PRIMARY KEY(`user_id`),
  CONSTRAINT userid_uc UNIQUE (`user_id`),
  CONSTRAINT email_uc UNIQUE (`email`),
  CONSTRAINT gender_chk CHECK(`gender` IN ('male','female')),
  CONSTRAINT password_chk CHECK(LENGTH(`password`)>0)
);

CREATE TABLE Friends (
  `user_id` int(11) NOT NULL,
  `friend_id` int(11) NOT NULL,
  CONSTRAINT userid_fk FOREIGN KEY(`user_id`) REFERENCES users(`user_id`),
  CONSTRAINT friendid_fk FOREIGN KEY(`friend_id`) REFERENCES users(`user_id`) 
);

CREATE TABLE Albums(
  `album_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `owner_id` int(11) NOT NULL,
  `date_created` date NOT NULL,
  CONSTRAINT albumid_pk PRIMARY KEY(`album_id`),
  CONSTRAINT ownerid_fk FOREIGN KEY(`owner_id`) REFERENCES users(`user_id`)
);


CREATE TABLE Pictures
(
  `picture_id` int(11) NOT NULL AUTO_INCREMENT,
  `album_id` int(255) NOT NULL,
  `imgdata` VARCHAR(255),
  `caption` VARCHAR(255),
  CONSTRAINT pictures_pk PRIMARY KEY (picture_id),
  CONSTRAINT pictureid_uc UNIQUE (`picture_id`),
  CONSTRAINT albumid_fk FOREIGN KEY(`album_id`) REFERENCES albums(`album_id`)
);

CREATE TABLE Tags(
  `picture_id` int(11) NOT NULL,
  `description` varchar(255) NOT NULL,
  CONSTRAINT pictureid_fk FOREIGN KEY(`picture_id`) REFERENCES Pictures(`picture_id`),
  CONSTRAINT description_chk CHECK(LENGTH(description)>0)
);

CREATE TABLE Comments(
  `comment_id` int(11) NOT NULL AUTO_INCREMENT,
  `owner_id` int(11) NOT NULL,
  `text` text NOT NULL,
  `date_left` date NOT NULL,
  `picture_id` int(11) NOT NULL,
  CONSTRAINT commentid_pk PRIMARY KEY(`comment_id`),
  CONSTRAINT owneridtwo_fk FOREIGN KEY(`owner_id`) REFERENCES users(`user_id`),
  CONSTRAINT photoidtwo_fk FOREIGN KEY(`picture_id`) REFERENCES Pictures(`picture_id`),
  CONSTRAINT text_chk CHECK(LENGTH(`text`)>0)
);


INSERT INTO Users (user_id, first_name, last_name, date_of_birth, email, hometown, gender, password) VALUES ('1111111111', 'testy', 'test', '1995-02-02', 'test@bu.edu', 'geogia', 'male', 'test');
INSERT INTO Users (user_id, first_name, last_name, date_of_birth, email, hometown, gender, password) VALUES ('1111111112', 'tester', 'testee', '1996-02-02', 'test2@bu.edu', 'geogia', 'female', 'test');
INSERT INTO Friends (user_id, friend_id) VALUES ('1111111111', '1111111112');
INSERT INTO Albums (name, owner_id, date_created) VALUES ('vahla', '1111111111', '2016-07-08');
INSERT INTO Pictures (album_id, imgdata, caption) VALUES ('1', 'path/to/image', 'testcap');
INSERT INTO Tags (picture_id, description) VALUES ('1', 'word');
INSERT INTO Comments (owner_id, text, date_left, picture_id) VALUES ('1111111111', 'LOL', '2016-07-08', '1');