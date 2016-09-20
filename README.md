# DLibrary

**Common library for VW plug-ins. It serves as a OOP wrapper around the vs calls and makes plugin development way 
easier, especially in setup and custom dialog creation.**

## USING THE LIBRARY

You can start using this library by adding it to the script paths in Vectorworks.

> There is a [Wiki](https://bitbucket.org/dieterdworks/vw-dlibrary/wiki/Home) with API docs and examples.

The library, and the wiki, aren't complete. This is an open-source project, so everyone can contribute and add stuff
that is missing and (s)he needs for her/his plugin. You can even contribute by just logging issues, requesting things,
or just give feedback. Everything is welcome!

### INSTALLATION

You'll find an `install.py` file with this library, to enable your users to install your plugin more easily and also 
install the minimum required version of dlibrary needed for your plugin to work. You just add this file to the .zip 
folder of your distribution for Vectorworks to pick it up.

> For manual install, please refer to `MANUAL_INSTALL.md`

**Due to a bug in Vectorworks, the PreInstall script in install.vwx, which is also included, has to be ran in order to 
prepare Vectorworks for the installation, as the script uses drop-in functions, which aren't available at start-up.**

## CONTRIBUTING

Everyone can contribute, and please do, so we can make this the best resource for Vectorworks plug-in developers to 
write great plug-ins fast and with ease! Just fork this repo and create a pull-request once you are done with your code.

### BRANCHES

#### The MASTER branch

The MASTER branch is our main branch with all versions tagged on it. So it will hold all versions of dlibrary. This will
reflect the releases of Vectorworks. For example, VW is now at version 2015, so we are also at version 2015. So through
the VW2015 version, we add to dlibrary for that version and make sure it stays backwards compatible. Off course there
can be code written for a future release and other code can be made obsolete, while still working! Once the next version
of Vectorworks is released, we do a cleanup of obsolete code and run all tests against the new vs api. We update our own
version to the new VW version and do an initial release. This process will continue throughout the whole MASTER branch.
This way, the user will only have one version of dlibrary for his VW installation with the same version number.
 
#### The HISTORY branches

Once we switch to the new VW version, we aren't able to do any more bugfixing for previous version, or add any new code
for people that really need it. VW itself doesn't do any more bugfixing of previous versions, but to give developers
time to update their code, and to still being able to satisfy users of older version, we'll need a way to apply bugfixes
and new features if needed. Therefore, before a new version is released, a HISTORY branch will be made for the old
version to make sure we can do bugfixes. The name of the branch should be `history/2015`.

#### The FEATURE branches

Writing a feature can take time and maybe isn't in time for the current release, also to make sure that there is enough
time to test etc, we'll need a way to work on a feature without breaking the MASTER branch. Therefore, for each feature
after the initial release, we'll work with FEATURE branches, named like `feature/feature-name`.

### CONTRIBUTION REMARKS

- Never use `_` for a throwaway variable, as VW seems to give special meaning to it!
- Keep in mind that for Singletons, they are unique for the VW sessions, not the script run!
- vs.py has been extended to add the things NNA didn't include like the Handle class. Make sure you leave this and check
when update the file with a new version!

### RELEASING

- Update the version number.
- Commit and tag the release.
- Create new version on Bitbucket.
- Update the wiki repo with new docs.
