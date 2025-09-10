module.exports = {
  presets: [
    ['next/babel', {
      typescript: {
        tsconfigPath: './tsconfig.json',
      },
    }],
  ],
};