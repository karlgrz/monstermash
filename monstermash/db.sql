-- sqlite3
create table user(
    id integer primary key,
    username TEXT unique,
	password TEXT,
    salt TEXT unique,
    role small integer default 0
);
insert into user (id, username, password, salt, role) values (0, 'Anonymous', '', '', 0); 

create table mash(
    id integer primary key, 
    user_id integer,
    key TEXT unique,
    song1 TEXT,
    song2 TEXT,
    status TEXT,
    FOREIGN KEY(user_id) references user(id)
);

-- mysql
CREATE TABLE user 
(
	`id` int(11) NOT NULL AUTO_INCREMENT, 	
	`username` varchar(32) NOT NULL, 
	`password` varchar(128) NOT NULL,
	`salt` varchar(32), 
	`role` smallint default 0, 
	PRIMARY KEY (`id`), 
	KEY `username` (`username`),
	KEY `role` (`role`)
);

insert into user (id, username, password, sale, role) values (0, 'Anonymous', '', '', 0);

create table mash 
(
	`id` int(11) NOT NULL AUTO_INCREMENT, 	
	`user_id` int(11) NOT NULL, 	
	`key` varchar(32) NOT NULL, 	
	`song1` varchar(256), 
	`song2` varchar(256), 
	`status` varchar(20), 
	PRIMARY KEY (`id`), 
	FOREIGN KEY(user_id) references user(id),
	KEY `user_id` (`user_id`), 
	KEY `key` (`key`),
	KEY `status` (`status`)
);
