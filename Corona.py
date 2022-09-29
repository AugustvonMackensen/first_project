import urllib.request, bs4
import matplotlib as mpl
import matplotlib.pyplot as plt
import common.oracle_db as oradb
import time

class Corona:
    # 지역 확진자 메소드
    def regional_case(self):
        page = urllib.request.urlopen('http://ncov.mohw.go.kr/bdBoardList_Real.do?brdId=1&brdGubun=13')
        result_code = bs4.BeautifulSoup(page, 'html.parser')
        regional_table = result_code.find('table', class_='num midsize')

        region_case_dict = {}
        try:
            for i in range(2, 19):
                rows = regional_table.select_one('tbody > tr:nth-child(' + str(i) + ')')
                region = rows.find('th').text
                case = int(rows.select_one('td:nth-child(5)').text.strip().replace(',', ''))
                region_case_dict[region] = case
            return region_case_dict
        except Exception as msg:
            print('크롤링 에러 발생 : ', msg)

    # 지역 사망자 메소드
    def regional_death(self):
        page = urllib.request.urlopen('http://ncov.mohw.go.kr/bdBoardList_Real.do?brdId=1&brdGubun=13')
        result_code = bs4.BeautifulSoup(page, 'html.parser')
        regional_table = result_code.find('table', class_='num midsize')
        region_death_dict = {}
        try:
            for i in range(2, 19):
                rows = regional_table.select_one('tbody > tr:nth-child(' + str(i) + ')')
                region = rows.find('th').text
                death = int(rows.select_one('td:nth-child(6)').text.strip().replace(',', ''))
                region_death_dict[region] = death
            return region_death_dict
        except Exception as msg:
            print('크롤링 에러 발생 : ', msg)

    def domestic_daily_case(self):
        page = urllib.request.urlopen('http://ncov.mohw.go.kr/bdBoardList_Real.do?brdId=1&brdGubun=11')
        result_code = bs4.BeautifulSoup(page, 'html.parser')
        header = result_code.select_one('#content > div > div:nth-child(14) > table > thead > tr')
        case_row = result_code.select_one('#content > div > div:nth-child(14) > table > tbody > tr:nth-child(1)')
        daily_case_dict = {}
        try:
            for item in range(2, 9):
                day = '2022' + header.select_one('th:nth-child(' + str(item) + ')').text.strip().replace('.', '')
                dc = int(case_row.select_one('td:nth-child(' + str(item) + ')').text.strip().replace(',', ''))
                daily_case_dict[day] = dc
            return daily_case_dict
        except Exception as msg:
            print('크롤링 에러 발생 : ', msg)

    def domestic_daily_death(self):
        page = urllib.request.urlopen('http://ncov.mohw.go.kr/bdBoardList_Real.do?brdId=1&brdGubun=11')
        result_code = bs4.BeautifulSoup(page, 'html.parser')
        header = result_code.select_one('#content > div > div:nth-child(14) > table > thead > tr')
        death_row = result_code.select_one('#content > div > div:nth-child(7) > table > tbody > tr:nth-child(1)')
        daily_death_dict = {}
        try:
            for item in range(2, 9):
                day = '2022' + header.select_one('th:nth-child(' + str(item) + ')').text.strip().replace('.', '')
                dd = int(death_row.select_one('td:nth-child(' + str(item) + ')').text.strip().replace(',', ''))
                daily_death_dict[day] = dd
            return daily_death_dict
        except Exception as msg:
            print('크롤링 에러 발생 : ', msg)

    def total_domestic_case(self):
        page = urllib.request.urlopen('http://ncov.mohw.go.kr/bdBoardList_Real.do?brdId=1&brdGubun=11')
        result_code = bs4.BeautifulSoup(page, 'html.parser')
        contents = result_code.select_one('#content > div > div:nth-child(17) > table > tbody')
        total_case_dict = {}
        try:
            for i in range(1, 8):
                day = contents.select_one('tr:nth-child(' + str(i) + ')>td:nth-child(1)').text
                tc = int(contents.select_one('tr:nth-child(' + str(i) + ')>td:nth-child(2)').text)
                total_case_dict[day] = tc
            return total_case_dict
        except Exception as msg:
            print('크롤링 에러 발생 : ', msg)

corona = Corona()

# db 저장
class CovidDB:
    def regional_db(self):
        r = Corona.regional_case(self).keys()
        c = Corona.regional_case(self).values()
        d = Corona.regional_death(self).values()

        r_list = []
        for item in zip(r, c, d):
            r_list.append(item)
        conn = oradb.connect()
        cursor = conn.cursor()
        try:
            # query = "insert into covid_region values(to_char(sysdate,'rrrrmmdd'), :1, :2, :3)"
            query = '''merge into covid_region
                                    using dual on (regdate = to_char(sysdate,'rrrrmmdd') AND region = :1)
                                    when matched then
                                        update set regcase = :2, regdeath = :3
                                    when not matched then
                                        insert(regdate, region, regcase, regdeath)
                                        values(to_char(sysdate,'rrrrmmdd'), :1, :2, :3)
                                    '''
            cursor.executemany(query, r_list)
            cursor.close()
            conn.commit()
            conn.close()
        except Exception as msg:
            oradb.rollback(conn)
            print('DB 저장 에러 : ', msg)

    # 국내 코로나 현황
    def domestic_db(self):
        days = Corona.domestic_daily_case(self).keys()
        dailycase = Corona.domestic_daily_case(self).values()
        totalcase = Corona.total_domestic_case(self).values()
        dailydeath = Corona.domestic_daily_death(self).values()
        d_list = []

        for item in zip(days, dailycase, totalcase, dailydeath):
            d_list.append(item)


        conn = oradb.connect()
        cursor = conn.cursor()
        try:
            query = '''merge into covid_domestic
                        using dual on (covdate = :1)
                        when matched then
                            update set daily_case = :2, total_case = :3, daily_death = :4
                        when not matched then
                            insert(covdate, daily_case, total_case, daily_death)
                            values(:1, :2, :3, :4)
                        '''
            cursor.executemany(query, d_list)
            cursor.close()
            conn.commit()
            conn.close()
        except Exception as msg:
            oradb.rollback(conn)
            print('DB 저장 에러 : ', msg)


covdb = CovidDB()

class CovidChart:
    # 폰트 설정
    mpl.rc('font', family='NanumGothic')
    mpl.rc('axes', unicode_minus=False)

    # 일일 확진자 그래프
    def domcase_chart(self):
        case_dict = Corona.domestic_daily_case(self)
        x = case_dict.keys()
        y = case_dict.values()

        fig, ax = plt.subplots(figsize=(10,5))

        ax.plot(x, y, color='blue', label='확진자')
        plt.xlabel('날짜')
        plt.ylabel('확진자 수')
        plt.title('일일 확진 현황')
        plt.legend(loc='best')
        plt.savefig(time.strftime('../../../project/easyway/static/charts/dailycase_%y%m%d.png'))
        plt.close(fig)

    # 일일 사망자 그래프
    def domdeath_chart(self):
        death_dict = Corona.domestic_daily_death(self)
        x = death_dict.keys()
        y = death_dict.values()

        fig, ax = plt.subplots(figsize=(10,5))

        ax.plot(x, y, color='red', label='사망자')
        plt.xlabel('날짜')
        plt.ylabel('사망자 수')
        plt.title('일일 사망 현황')
        plt.legend(loc='best')
        plt.savefig(time.strftime('../../../project/easyway/static/charts/dailydeath_%y%m%d.png'))
        plt.close(fig)

    # 1주일간 국내 확진 현황t
    def totcase_chart(self):
        totcase_dict = Corona.total_domestic_case(self)
        x = totcase_dict.keys()
        y = totcase_dict.values()

        fig, ax = plt.subplots(figsize=(10,5))

        ax.plot(x, y, color='blue', label='누적확진자')
        plt.xlabel('날짜')
        plt.ylabel('누적 확진자 수')
        plt.title('누적 확진 현황')
        plt.ticklabel_format(style='plain', axis='y')
        plt.legend(loc='best')
        plt.savefig(time.strftime('../../../project/easyway/static/charts/totalcase_%y%m%d.png'))
        plt.close(fig)

    # 지역 코로나 발생현황 그래프
    def region_chart(self):
        case_dict = Corona.regional_case(self)
        death_dict = Corona.regional_death(self)
        x = case_dict.keys()
        y1 = case_dict.values()
        y2 = death_dict.values()

        fig, ax1 = plt.subplots(figsize=(10,5))

        ax1.bar(x, y1, color='blue', alpha=0.7, label='확진자', width=0.9)
        ax1.set_xlabel('지역')
        ax1.set_ylabel('확진자 수')
        ax1.set_ylim(0, 6000000)
        ax1.ticklabel_format(style='plain', axis='y')
        ax1.tick_params(axis='both', direction='in')

        ax2 = ax1.twinx()
        ax2.plot(x, y2, color='red', linewidth=3, alpha=0.7, label='사망자)')
        ax2.set_ylabel('사망자 수')
        ax2.set_ylim(0, 10000)
        ax2.tick_params(axis='y', direction='in')
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')
        plt.title('지역별 코로나 현황')
        plt.savefig(time.strftime('../../../project/easyway/static/charts/regional_chart_%y%m%d.png'))
        plt.close(fig)

covidchart = CovidChart()
