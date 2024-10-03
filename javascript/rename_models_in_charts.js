/**
 * This script will rename all the models in charts in spaces
 * That includes dimensions, metrics, filters, sorts, tableConfig, chartConfig and table calculations
 * 
 * This script will not update
 * conditional formatting,reference lines, dashboards, dashboard filters, charts within dashboards
 */

import fetch from 'node-fetch';

const projectUuid = `3675b69e-8324-4110-bdca-059031aa8da3` // Replace me
const apiKey = 'ae1d564a496cea41f74de7ffd920f724' // Replace me
const oldModel = 'customers' // Replace me
const newModel = 'users' // Replace me
const testing = true // set to false to actually update the charts
const debug = false // Enable this to see more logs 

const apiUrl = 'http://localhost:3000/api/v1'

const headers = {
    "Authorization": `ApiKey ${apiKey}`,
    'Content-Type': 'application/json'
}

const replaceModelPrefix = (dimension) => {
    // This function only works if oldModel is a prefix of newModel
    // otherwise it will do nothing
    // This is to avoid replacing the same model multiple times
    if(!dimension || dimension.includes(newModel)) return dimension // Already replaced
    return dimension.replace(new RegExp(`${oldModel}`, 'g'), `${newModel}`)
}

function renameKeys(obj) {
    const keyValues = Object.keys(obj).map(key => {
      const newKey = replaceModelPrefix(key)
      return { [newKey]: obj[key] };
    });
    return Object.assign({}, ...keyValues);
  }

const replaceChartConfig = (chartConfig) => {
    switch(chartConfig.type){
        case 'table':

            if (!chartConfig.config) return chartConfig
            return {...chartConfig,
                config: {
                    ...chartConfig.config,
                    columns: renameKeys(chartConfig.config?.columns) ,
                    conditionalFormattings: chartConfig.config.conditionalFormattings?.map((conditionalFormatting) => {
                        return {
                            ...conditionalFormatting,
                            target: {
                                ...conditionalFormatting.target,
                                fieldId: replaceModelPrefix(conditionalFormatting.target.fieldId)
                            }
                        }
                    })
                },
            }
        case 'cartesian': 
            return {
                ...chartConfig,
                config: {
                    ...chartConfig.config,
                    layout: {
                        ...chartConfig.config.layout,
                        xField: replaceModelPrefix(chartConfig.config.layout.xField),
                        yField: chartConfig.config.layout.yField?.map(replaceModelPrefix),
                    },
                    eChartsConfig: {
                        ...chartConfig.config.eChartsConfig,
                        series: chartConfig.config.eChartsConfig.series?.map((serie) => {
                            return {
                                ...serie,
                                encode: {
                                    ...serie.encode,
                                    xRef: {
                                        ...serie.encode.xRef,
                                        field: replaceModelPrefix(serie.encode.xRef.field)},
                                    yRef:  {
                                        ...serie.encode.yRef,
                                        field: replaceModelPrefix(serie.encode.yRef.field)},
                                }
                            }
                        })
                    }
                }
            }
        case 'big_number':

            return {...chartConfig, 
            config: {
                ...chartConfig.config,
                selectedField: replaceModelPrefix(chartConfig.config.selectedField)
            }}

        default: 
            console.warn('Unknown chart type', chartConfig.type)
            return chartConfig
    }
}
const replaceFilters = (filters) => {
    if (!filters || Object.keys(filters).length  === 0) {
        return filters
    } else if ('dimensions' in filters  || 'metrics' in filters) {
        return {
            ...filters, 
            dimensions: replaceFilters(filters.dimensions),
            metrics: replaceFilters(filters.metrics)
        }
        
    }  else if ('and' in filters) {
        return {
            ...filters, 
            and: filters.and.map(replaceFilters) 
        }
    } else if ('or' in filters) {
        return {
            ...filters, 
            or: filters.or.map(replaceFilters) 
        }
    } else if ('target' in filters) {
        return {
            ...filters,
            target: {
                ...filters.target,
                fieldId: replaceModelPrefix(filters.target.fieldId)
            }
        }
    } else {
        throw new Error(`Invalid filter format ${JSON.stringify(filters)}, ${filters}`)
    }


}
const rename = async () => {
    if (debug) console.log('Making request to get space summaries')
    const spaceSummaryFetch = await fetch(`${apiUrl}/projects/${projectUuid}/spaces`, {
        method: 'GET',
        headers,
    });
    if (debug) console.log('Space summary response', spaceSummaryFetch.status)

    const spaceResponse = await  spaceSummaryFetch.json()
    console.log('This project has '+spaceResponse.results.length+' spaces' )

    spaceResponse.results.map(async (spaceSummary) => {
        if (debug) console.log(`Making request to get space ${spaceSummary.uuid}`)

        const spaceFetch = await fetch(`${apiUrl}/projects/${projectUuid}/spaces/${spaceSummary.uuid}`, {
            method: 'GET',
            headers,
        });
        if (debug) console.log('Space response', spaceFetch.status)

        const space = (await spaceFetch.json()).results
        console.log(`Space ${space.name} has ${space.queries.length} charts and ${space.queries.dashboards} dashboards` )

        space.queries.map(async (query) => {
            if (debug) console.log(`Making request to get chart ${query.uuid}`)
            let savedChart = undefined
            let savedChartResponse = undefined

            try {
                const savedChartUuid = query.uuid 

                const savedChartFetch = await fetch(`${apiUrl}/saved/${savedChartUuid}`, {
                    method: 'GET',
                    headers,
                });
                
                savedChartResponse = await savedChartFetch.json()

                savedChart = savedChartResponse.results
                const newChart = {
                    ...savedChart, 
                    tableName: savedChart.tableName.replace(new RegExp(`^${oldModel}$`, 'g'), newModel),
                    tableConfig: {
                        ...savedChart.tableConfig, 
                        columnOrder: savedChart.tableConfig.columnOrder.map(replaceModelPrefix)
                    },
                    
                    chartConfig: replaceChartConfig(savedChart.chartConfig),
                    metricQuery: {
                        ...savedChart.metricQuery,
                        dimensions: savedChart.metricQuery.dimensions.map(replaceModelPrefix),
                        metrics: savedChart.metricQuery.metrics.map(replaceModelPrefix),
                        filters: replaceFilters(savedChart.metricQuery.filters),
                        tableCalculations: savedChart.metricQuery.tableCalculations?.map(tc => ({...tc, sql: replaceModelPrefix(tc.sql)})),
                        sorts: savedChart.metricQuery.sorts.map((sort) => ({...sort, fieldId: replaceModelPrefix(sort.fieldId)}) ),
                    }
                }

                const hasChanges = JSON.stringify(savedChart) !== JSON.stringify(newChart)

                if (!hasChanges) {
                    console.log(`chart ${savedChart.name} has no changes`)
                    return 
                }else {
                    console.log(`--------------chart ${savedChart.name} (${savedChartUuid}) has changes ---------`)
                    console.info(JSON.stringify(savedChart)   )
                    console.log('------')
                    console.info(JSON.stringify(newChart)  )
                    console.log('------')
                }

                if (debug) {
                    console.log('replacing tableName ', savedChart.tableName , 'with', newChart.tableName)
                    console.log('replacing tableConfig ', savedChart.tableConfig , 'with', newChart.tableConfig)
                    console.log('replacing metricQuery.dimensions ', savedChart.metricQuery.dimensions , 'with', newChart.metricQuery.dimensions)
                    console.log('replacing filters ', savedChart.metricQuery.filters , 'with', newChart.metricQuery.filters)
                    console.log('replacing tableCalculations ', savedChart.metricQuery.tableCalculations , 'with', newChart.metricQuery.tableCalculations)

                    console.log('updating new chart', newChart)
                }
                if (testing===false){

                    const updateResponse = await fetch(`${apiUrl}/saved/${savedChartUuid}/version`, {
                        method: 'POST',
                        headers,
                        body: JSON.stringify(newChart) 
                    });
                    console.log(`Chart updated ${savedChartUuid}: response status ${updateResponse.status}`)

                }
            } catch (e) {
                console.error('------------------')
                if (!savedChart) {
                    console.error(`Error fetching chart ${query.uuid}`, e)
                    if (debug) {
                        console.error('here is a snippet of the query saved in the space: ')
                        console.error(JSON.stringify(query, null, 2))
                        console.error('------')
                        console.error('here is a reseponse from the server: ')
                        console.error(JSON.stringify(savedChartResponse, null, 2))
                    }
                } else {
                    console.error(`Error updating chart "${savedChart.name}", consider removing this chart or updating manually`, e)
                    if (debug) {
                        console.error('here is a snippet of the chart: ')
                        console.error(JSON.stringify(savedChart, null, 2))
                    }
                }
                console.error('------------------')
            }
        })
    })
}

rename()