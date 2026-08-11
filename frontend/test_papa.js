const Papa = require('papaparse');
const text = `query,documents,answer
What is the capital of France?,"Paris is the capital of France|France is in Europe",The capital is Paris`;

const result = Papa.parse(text, { header: true, skipEmptyLines: true });
console.log(result.data);
