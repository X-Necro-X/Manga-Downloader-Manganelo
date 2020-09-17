# imports
import os, time, requests
from PIL import Image
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
base_path = os.path.dirname(__file__)
options = webdriver.ChromeOptions()
# driver settings
options.add_argument('--start-maximized')
options.add_argument('--log-level=OFF')
options.add_argument('--disable-web-security')
options.add_experimental_option('prefs', {'profile.default_content_setting_values.automatic_downloads': 1, 'download.default_directory': base_path+'\\downloads'})
# download chrome driver if not present
if not(os.path.exists(base_path+'\\chromedriver.exe')):
    print('Downloading chromedriver.exe(9.16MB)...')
    with open(base_path+'\\chromedriver.exe', 'wb') as exe:
        exe.write(requests.get('https://drive.google.com/uc?id=1rbpJrnDiF37tApPro29pymC9WHY_P7xz').content)
    print('Download Complete!')
try:
    driver = webdriver.Chrome(executable_path=base_path+'\\chromedriver.exe', options = options)
    # script to download image
    script = '''
        function imgLoad(url) {{
            return new Promise(function (resolve, reject) {{
                var request = new XMLHttpRequest();
                request.open('GET', url);
                request.responseType = 'blob';
                request.onload = function () {{
                    if (request.status === 200) {{
                        resolve(request.response);
                    }} else {{
                        reject(Error('Error code:' + request.statusText));
                    }}
                }};
                request.onerror = function () {{
                    reject(Error('There was a network error.'));
                }};
                request.send();
            }});
        }}
        function sleep() {{
            return new Promise(resolve => setTimeout(resolve, 100));
        }}
        imgLoad('{url}')
            .then(async function (response) {{
                var a = document.createElement("a");    
                a.style = "display: none";
                a.href = window.URL.createObjectURL(response);
                a.download = "{name}";
                a.id = "event{name}";
                a.click();
                await sleep();
                document.body.appendChild(a);
            }},
            function (Error) {{
                console.log(Error);
            }});
    '''
    # creating downloads and image directories
    os.system(base_path[:2]+'&cd '+base_path+'&rmdir /Q /S downloads&mkdir downloads&cd downloads&echo.> img.png&cd ..&mkdir manga')
    manga_url = input('Enter manga URL:\n').strip()
    driver.get(manga_url)
    # extracting chapter urls
    chapters = list(map(lambda x: [x.text, x.get_attribute('href')], driver.find_elements_by_class_name('chapter-name')))[::-1]
    downloaded_chapters = os.listdir(base_path+'\\manga')
    for chapter in chapters:
        # os friendly file names
        chapter_name = chapter[0].replace('&', 'and').replace('/', '~').replace(':', '~').replace('*', '~').replace('?', '~').replace('"', '~').replace('<', '~').replace('>', '~').replace('|', '~')
        # check if a chapter is already downloaded
        if chapter_name+'.pdf' in downloaded_chapters:
            continue
        pdf = []
        driver.get(chapter[1])
        # extracting image urls
        images = list(map(lambda x: x.get_attribute('src'), driver.find_elements_by_tag_name('img')[1:-1]))
        for image in range(len(images)):
            # adding 00 and 0 before single and double digit image numbers respectively
            name = '00'+str(image) if image<10 else '0'+str(image) if image<100 else str(image)
            # executing script to download image
            driver.execute_script(script.format(url = images[image], name = name+'.png'))
            # waiting for download to finish
            WebDriverWait(driver, 100).until(EC.presence_of_element_located((By.ID, 'event'+name+'.png')))
        time.sleep(5)
        # check if all the images are downloaded
        if(len(os.listdir(base_path+'\\downloads')[:-1]) != len(images)):
            print('An error occurred in downloading: '+chapter[0]+'\nPlease restart!')
            break
        for image in os.listdir(base_path+'\\downloads')[:-1]:
            im = Image.open(base_path+'\\downloads\\'+image).convert('RGB')
            pdf.append(im)
        # saving chapter as pdf
        pdf[0].save(base_path+'\\manga\\'+chapter_name+'.pdf', 'PDF', resolution=100.0, save_all=True, append_images=pdf[1:])
        # reset downloads folder for next chapter
        os.system(base_path[:2]+'&cd '+base_path+'&rmdir /Q /S downloads&mkdir downloads&cd downloads&echo.> img.png')
except Exception as e:
    print('An error occurred: '+e+'\nPlease restart!')
driver.close()