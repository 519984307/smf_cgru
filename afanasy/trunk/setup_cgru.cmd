rem   Try to setup CGRU (if will be founded):

IF NOT DEFINED CGRU_LOCATION (
	PUSHD ..
   if not exist setup.cmd cd ..
   if not exist setup.cmd cd ..
   if not exist setup.cmd cd ..
   if not exist setup.cmd cd ..
	if exist setup.cmd call setup.cmd
	POPD
)
