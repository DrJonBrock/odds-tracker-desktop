import { BaseDirectory, createDir, readTextFile, writeTextFile } from '@tauri-apps/api/fs';

export const saveData = async (data) => {
  try {
    await createDir('odds-tracker', { dir: BaseDirectory.AppData, recursive: true });
    await writeTextFile(
      'odds-tracker/data.json',
      JSON.stringify(data),
      { dir: BaseDirectory.AppData }
    );
  } catch (error) {
    console.error('Error saving data:', error);
  }
};

export const loadData = async () => {
  try {
    const contents = await readTextFile(
      'odds-tracker/data.json',
      { dir: BaseDirectory.AppData }
    );
    return JSON.parse(contents);
  } catch (error) {
    console.error('Error loading data:', error);
    return null;
  }
};