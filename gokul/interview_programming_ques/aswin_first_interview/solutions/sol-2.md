## use js
your input will be 12 digit number, you need to give a space after every 4 digits while printing.

INPUT : '123456789121' 
OUTPUT : '1234 5678 9121'

SOL:
```js
function splitNumber(num) {
    let str = num.toString();
    let result = '';
    for (let i = 0; i < str.length; i++) {
        if (i % 4 === 0 && i !== 0) {
            result += ' ';
        }
        result += str[i];
    }
    return result;
}

console.log(splitNumber(123456789121));
```