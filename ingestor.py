import pyart
from os.path import exists
from matplotlib import pyplot as plt
from datetime import datetime
import nexradaws

def save_file(conn, year, month, day, radar_id):
    filename = f"{year}-{month}-{day}-{radar_id}.png"

    # a plot is unique for a combination of date and radar_id
    if exists(filename):
        return filename

    avail_scans = conn.get_avail_scans(year, month, day, radar_id)

    # ignore MDM files
    avail_scans = [scan for scan in avail_scans if scan.filename.find('MDM') == -1]

    # Compute indices that will be used to generate plots
    quartile_index = len(avail_scans) // 4
    three_quartile_index = quartile_index * 3

    considered_scans = []
    considered_scans.append(avail_scans[0])
    considered_scans.append(avail_scans[quartile_index])
    considered_scans.append(avail_scans[three_quartile_index])
    considered_scans.append(avail_scans[len(avail_scans) - 1])
    res = conn.download(considered_scans, './')

    print(res.success)

    fig = plt.figure(figsize=(16,12))

    fig.suptitle(f"Reflectivity pattern for {radar_id} radar on {year}-{month}-{day}", fontweight='bold')

    times = ['After midnight', 'Early morning', 'Evening', 'Late Night']

    for i,scan in enumerate(res.iter_success(),start=1):
        ax = fig.add_subplot(2,2,i)
        radar = scan.open_pyart()
        display = pyart.graph.RadarDisplay(radar)
        display.plot('reflectivity', 0, title=f"{scan.radar_id} {scan.scan_time} ({times[i - 1]})",
                    vmin=-32, vmax=64, colorbar_label='', ax=ax)
        display.plot_range_ring(radar.range['data'][-1]/1000., ax=ax)
        display.set_limits(xlim=(-500, 500), ylim=(-500, 500), ax=ax)

    plt.savefig(filename)

    return filename

if __name__ == "__main__":
    conn = nexradaws.NexradAwsInterface()
    save_file(conn, '2018', '06', '07', 'KTLX')



