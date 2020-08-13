var ngClassify = require('ng-classify');
var fs = require('fs')

// List all files in a directory in Node.js recursively in a synchronous fashion
var walkSync = function(dir, filelist) {
	var files = fs.readdirSync(dir);
	filelist = filelist || [];
	files.forEach(function(file) {
	  if (fs.statSync(dir + file).isDirectory()) {
		filelist = walkSync(dir + file + '/', filelist);
	  }
	  else {
		  if (file.endsWith(".coffee"))
			filelist.push(dir + file);
	  }
	});
	return filelist;
  };
walkSync("./").forEach((x) => {
	var content = fs.readFileSync(x, {encoding: 'utf-8'});
	content = ngClassify(content);
	fs.writeFileSync(x, content, {encoding: 'utf-8'});
})
