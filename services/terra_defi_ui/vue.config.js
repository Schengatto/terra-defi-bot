const path = require("path");

module.exports = {
  outputDir: path.resolve(__dirname, "./dist"),
  configureWebpack: (config) => {
    config.output.filename = '[name].[hash:8].js';
    config.output.chunkFilename = '[name].[hash:8].js';
    }
}