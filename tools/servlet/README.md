# arat servlet #

This is a full-fledged arat CGI servlet to deploy arat on Tomcat. While this
is a bit of an exotic usecase, it is an existing one and this README along
with the XML provided should keep you from crying your eyes out while solving
this exercise.

# Building #

First, some words on how this works. You will attempt to create a WAR (Web
application ARchive) containing a working arat installation. This means you
will first have to install arat as usual and deploy your data. Create the arat
folder structure as shown (`arat/WEB-INF`, `arat/META-INF`) with the given
`web.xml` and `context.xml`. Copy your previously installed arat installation
to `arat/`, then, proving that you don't need ant to build something Java-ish,
simply go to the parent folder of `arat`, where the `GNUmakefile` is, and run:

    make

This will produce an archive `arat.war` that you can deploy on Tomcat.

# Installation #

Drop the `arat.war` into the Tomcat `webapps` directory and you should be able
to access your installation using:

    http://${HOSTNAME}:${PORT}/arat/

From now on, arat should work as usual with the exception that it is Tomcat
serving your requests.
