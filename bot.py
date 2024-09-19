import logging
import subprocess
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# إعداد تسجيل الدخول
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# دالة لفحص الدومين باستخدام subfinder
def subfinder(domain):
    try:
        result = subprocess.run(['subfinder', '-d', domain], capture_output=True, text=True)
        return result.stdout.strip().splitlines()
    except Exception as e:
        return [str(e)]

# دالة لفحص الدومين باستخدام httpx
def httpx_scan(subdomains):
    results = []
    for subdomain in subdomains:
        try:
            result = subprocess.run(['httpx', '-l', f'http://{subdomain}'], capture_output=True, text=True)
            results.append((subdomain, result.stdout.strip().splitlines()))
        except Exception as e:
            results.append((subdomain, [str(e)]))
    return results

# دالة لفحص الدومين باستخدام ffuf
def ffuf_scan(subdomains):
    results = []
    for subdomain in subdomains:
        try:
            result = subprocess.run(['ffuf', '-u', f'http://{subdomain}/FUZZ', '-w', '/path/to/wordlist.txt'], capture_output=True, text=True)
            results.append((subdomain, result.stdout.strip().splitlines()))
        except Exception as e:
            results.append((subdomain, [str(e)]))
    return results

# دالة لفحص الدومين باستخدام dalfox
def dalfox_scan(subdomains):
    results = []
    for subdomain in subdomains:
        try:
            result = subprocess.run(['dalfox', 'url', f'http://{subdomain}'], capture_output=True, text=True)
            if result.stdout.strip():
                results.append((subdomain, result.stdout.strip().splitlines()))
        except Exception as e:
            results.append((subdomain, [str(e)]))
    return results

# دالة لفحص الدومين باستخدام subz
def subz_scan(subdomains):
    results = []
    for subdomain in subdomains:
        try:
            result = subprocess.run(['subz', subdomain], capture_output=True, text=True)
            if result.stdout.strip():
                results.append((subdomain, result.stdout.strip().splitlines()))
        except Exception as e:
            results.append((subdomain, [str(e)]))
    return results

# دالة لفحص الدومين باستخدام nuclei مع دعم القوالب
def nuclei_scan(subdomains, templates=None):
    results = []
    for subdomain in subdomains:
        try:
            command = ['nuclei', '-u', f'http://{subdomain}']
            if templates:
                command += ['-t', templates]  # إضافة القوالب المحددة
            result = subprocess.run(command, capture_output=True, text=True)
            if result.stdout.strip():
                results.append((subdomain, result.stdout.strip().splitlines()))
        except Exception as e:
            results.append((subdomain, [str(e)]))
    return results

# دالة لمعالجة الرسائل
def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text('أرسل لي دومين أو عدة دومينات مفصولة بفاصلة أو مسافة وسأقوم بفحصها.')

def check_domain(update: Update, context: CallbackContext) -> None:
    domains_input = update.message.text.strip()
    
    # تقسيم الدومينات إلى قائمة
    domains = [domain.strip() for domain in domains_input.replace(',', ' ').split() if domain.strip()]
    
    if domains:
        update.message.reply_text('جاري فحص الدومينات...')
        
        final_response = "### نتائج الفحص ###\n\n"
        
        for domain in domains:
            final_response += f"#### فحص الدومين: {domain} ####\n"
            
            # استخدم subfinder للحصول على الدومينات الفرعية
            subdomains = subfinder(domain)
            
            # استخدم httpx على الدومينات الفرعية
            httpx_results = httpx_scan(subdomains)
            # استخدم dalfox على الدومينات الفرعية
            dalfox_results = dalfox_scan([sub[0] for sub in httpx_results])

            # استخدم subz على الدومينات الفرعية
            subz_results = subz_scan([sub[0] for sub in httpx_results])

            # طلب القوالب من المستخدم لـ nuclei
            templates = context.args[0] if context.args else None  # استخدام القالب الأول من الأرجومنتات
            
            # استخدم nuclei على الدومينات الفرعية
            nuclei_results = nuclei_scan([sub[0] for sub in httpx_results], templates)
            
            # تنسيق النتائج لكل دومين
            final_response += "#### الدومينات الفرعية ####\n"
            final_response += "\n".join(subdomains) + "\n\n"

            # عرض نتائج Dalfox إذا كانت موجودة
            if dalfox_results:
                final_response += "#### نتائج Dalfox ####\n"
                for subdomain, res in dalfox_results:
                    final_response += f"{subdomain}:\n" + "\n".join(res) + "\n\n"

            # عرض نتائج SubZ إذا كانت موجودة
            if subz_results:
                final_response += "#### نتائج SubZ ####\n"
                for subdomain, res in subz_results:
                    final_response += f"{subdomain}:\n" + "\n".join(res) + "\n\n"

            # عرض نتائج Nuclei إذا كانت موجودة
            if nuclei_results:
                final_response += "#### نتائج Nuclei ####\n"
                for subdomain, res in nuclei_results:
                    final_response += f"{subdomain}:\n" + "\n".join(res) + "\n\n"
        
        update.message.reply_text(final_response)

def main() -> None:
    # استبدل 'YOUR_TOKEN' بالتوكن الخاص بك
    updater = Updater("YOUR_TOKEN")

    dispatcher = updater.dispatcher

    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, check_domain))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
