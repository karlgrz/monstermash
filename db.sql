create table user(
	id integer primary key,
	nickname TEXT unique,
	email TEXT unique,
	role small integer default 0
);

create table mash(
	id integer primary key,	
	userid integer,
	key TEXT unique,
	song1 TEXT,
	song2 TEXT,
	status TEXT,
	FOREIGN KEY(userid) references user(id)
);
