function getDateDifferenceInSecs(date1, date2) {
    return (date1.getTime() - date2.getTime()) / 1000;
}

function bytesToSize(bytes) {
    if      (bytes >= 1073741824) { bytes = (bytes / 1073741824).toFixed(2) + " GB"; }
    else if (bytes >= 1048576)    { bytes = (bytes / 1048576).toFixed(2) + " MB"; }
    else if (bytes >= 1024)       { bytes = (bytes / 1024).toFixed(2) + " KB"; }
    else if (bytes > 1)           { bytes = bytes + " bytes"; }
    else if (bytes == 1)          { bytes = bytes + " byte"; }
    else                          { bytes = "0 bytes"; }
    return bytes;
}

function plotSizes(sizes) {
    let sizes_times = []
    let sizes_values = []
    console.log(sizes);
    for (let dt in sizes) {
        sizes_times.push(dt);
        sizes_values.push(sizes[dt]["total_size"]);
    }

    let plotlyData = [
        {
            x: sizes_times,
            y: sizes_values,
            type: 'scatter',
            yaxis: 'y2'
        }
    ];
    return {
        "plotlyData": plotlyData,
    };
}
