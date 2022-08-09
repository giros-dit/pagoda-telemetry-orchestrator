package upm.dit.giros.processors.prometheusmetadriver;

import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.rev211118.Metrics;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.rev211118.label.set.labels.LabelKey;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.rev211118.metric.point.set.metric.points.MetricPointsChoice;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.rev211118.metrics.Metric;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.rev211118.metrics.MetricKey;
import org.opendaylight.yang.gen.v1.urn.ietf.params.xml.ns.yang.ietf.yang.types.rev130715.DateAndTime;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.label.set.Labels;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.label.set.LabelsBuilder;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.label.set.labels.Label;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.label.set.labels.LabelBuilder;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.metric.point.set.MetricPoints;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.metric.point.set.MetricPointsBuilder;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.metric.point.set.metric.points.metric.points.choice.MetricPointList;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.metric.point.set.metric.points.metric.points.choice.MetricPointListBuilder;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.metric.point.set.metric.points.metric.points.choice.MetricPointSingle;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.metric.point.set.metric.points.metric.points.choice.MetricPointSingleBuilder;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.metric.point.set.metric.points.metric.points.choice.metric.point.list.MetricPoint;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.metric.point.set.metric.points.metric.points.choice.metric.point.list.MetricPointBuilder;
import org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.metric.point.set.metric.points.metric.points.choice.metric.point.list.MetricPointKey;

import java.io.*;
import java.math.BigDecimal;
import java.text.DateFormat;
import java.text.SimpleDateFormat;
import java.util.*;

import java.util.Map.Entry;
import java.util.concurrent.TimeUnit;

import com.fasterxml.jackson.databind.ser.std.StdKeySerializers.Default;
import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import com.google.gson.stream.JsonReader;
import com.google.gson.stream.JsonWriter;

import org.opendaylight.mdsal.binding.dom.codec.api.BindingNormalizedNodeSerializer;
import org.opendaylight.mdsal.binding.dom.codec.impl.BindingCodecContext;
import org.opendaylight.mdsal.binding.runtime.spi.BindingRuntimeHelpers;
import org.opendaylight.mdsal.binding.spec.reflect.BindingReflections;
import org.opendaylight.yangtools.yang.binding.InstanceIdentifier;
import org.opendaylight.yangtools.yang.data.api.YangInstanceIdentifier;
import org.opendaylight.yangtools.yang.data.api.schema.MapEntryNode;
import org.opendaylight.yangtools.yang.data.api.schema.NormalizedNode;
import org.opendaylight.yangtools.yang.data.api.schema.stream.NormalizedNodeStreamWriter;
import org.opendaylight.yangtools.yang.data.api.schema.stream.NormalizedNodeWriter;
import org.opendaylight.yangtools.yang.data.codec.gson.JSONCodecFactory;
import org.opendaylight.yangtools.yang.data.codec.gson.JSONCodecFactorySupplier;
import org.opendaylight.yangtools.yang.data.codec.gson.JSONNormalizedNodeStreamWriter;
import org.opendaylight.yangtools.yang.data.codec.gson.JsonParserStream;
import org.opendaylight.yangtools.yang.data.codec.gson.JsonWriterFactory;
import org.opendaylight.yangtools.yang.data.impl.schema.ImmutableNormalizedNodeStreamWriter;
import org.opendaylight.yangtools.yang.data.impl.schema.NormalizedNodeResult;
import org.opendaylight.yangtools.yang.model.api.EffectiveModelContext;
import org.opendaylight.yangtools.yang.model.api.SchemaPath;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

/**
 * Prometheus to PAGODA YANGTools Transformer Driver.
 */
public class PrometheusToPagodaTransformerDriver {
    
    // Code borrowed from:
    // https://git.opendaylight.org/gerrit/gitweb?p=jsonrpc.git;a=blob_plain;f=impl/src/
    // main/java/org/opendaylight/jsonrpc/impl/
    private static final String JSON_IO_ERROR = "I/O problem in JSON codec";
    private static final Logger LOG = LoggerFactory.getLogger(PrometheusToPagodaTransformerDriver.class);
    private static final JSONCodecFactorySupplier CODEC_SUPPLIER = JSONCodecFactorySupplier.RFC7951;
    private static final JsonParser PARSER = new JsonParser();
    private BindingNormalizedNodeSerializer codec;
    private EffectiveModelContext schemaContext;
    private JSONCodecFactory codecFactory;
  

    public PrometheusToPagodaTransformerDriver(){
        schemaContext = BindingRuntimeHelpers.createEffectiveModel(BindingReflections.loadModuleInfos());
        codec = new BindingCodecContext(BindingRuntimeHelpers.createRuntimeContext());
        codecFactory = CODEC_SUPPLIER.getShared(schemaContext);
    }

    /**
     * Performs the actual data conversion.
     *
     * @param schemaPath - schema path for data
     * @param data - Normalized Node
     * @return data converted as a JsonObject
     */
    private JsonObject doConvert(EffectiveModelContext schemaContext, SchemaPath schemaPath, NormalizedNode<?, ?> data) {
        try (StringWriter writer = new StringWriter();
                JsonWriter jsonWriter = JsonWriterFactory.createJsonWriter(writer)) {
            final NormalizedNodeStreamWriter jsonStream = (data instanceof MapEntryNode)
                    ? JSONNormalizedNodeStreamWriter.createNestedWriter(codecFactory, schemaPath, null, jsonWriter)
                    : JSONNormalizedNodeStreamWriter.createExclusiveWriter(codecFactory, schemaPath, null, jsonWriter);
            try (NormalizedNodeWriter nodeWriter = NormalizedNodeWriter.forStreamWriter(jsonStream)) {
                nodeWriter.write(data);
                nodeWriter.flush();
            }
            return PARSER.parse(writer.toString()).getAsJsonObject();
        } catch (IOException e) {
            LOG.error(JSON_IO_ERROR, e);
            return null;
        }
    }
    
    public String driver(JsonReader reader){
        NormalizedNodeResult result = new NormalizedNodeResult();
        NormalizedNodeStreamWriter streamWriter = ImmutableNormalizedNodeStreamWriter.from(result);
        JsonParserStream jsonParser = JsonParserStream.create(streamWriter, codecFactory);
        jsonParser.parse(reader);
        NormalizedNode<?, ?> transformedInput = result.getResult();
        InstanceIdentifier<Metrics> prometheus_iid = InstanceIdentifier.create(Metrics.class);
        YangInstanceIdentifier prometheus_yiid = codec.toYangInstanceIdentifier(prometheus_iid);
        Metrics prom_metrics = (Metrics) codec.fromNormalizedNode(prometheus_yiid, transformedInput).getValue();
        // Instantiate PAGODA MetricsBuilder object
        org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.MetricsBuilder pagoda_metricsBuilder = new org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.MetricsBuilder();
        // Instantiate array list object for Prometheus metrics
        ArrayList<org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.metrics.Metric> pagoda_metric_list = new ArrayList<org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.metrics.Metric>();

        // Mapping/translate Prometheus labels to PAGODA labels
        for (Map.Entry<MetricKey, Metric> prom_metric: prom_metrics.getMetric().entrySet()){
            
            // Instantiate PAGODA MetricPointSingleBuilder object to record single Prometheus metric or list of Prometheus metric data
            MetricPointsBuilder metricPointsBuilder = new MetricPointsBuilder();

            MetricPointsChoice metricPointsChoice = prom_metric.getValue().getMetricPoints().getMetricPointsChoice();
            if(metricPointsChoice instanceof org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.rev211118.metric.point.set.metric.points.metric.points.choice.MetricPointSingle){
                org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.rev211118.metric.point.set.metric.points.metric.points.choice.MetricPointSingle metricPointSingle = (org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.rev211118.metric.point.set.metric.points.metric.points.choice.MetricPointSingle) metricPointsChoice;
                BigDecimal timestamp = metricPointSingle.getTimestamp();
                BigDecimal value = metricPointSingle.getValue();
                // Instantiate Prometheus MetricPointSingleBuilder object to record single Prometheus metric data
                MetricPointSingleBuilder metricPointBuilder = new MetricPointSingleBuilder();
                // Translate Prometheus metric timestamp
                //Long nano2milli = TimeUnit.MILLISECONDS.toMillis(Long.parseLong(timestamp.toString()));
                Long milliseconds = timestamp.multiply(new BigDecimal(1000)).longValue();
                DateFormat df = new SimpleDateFormat("Y-MM-dd'T'HH:mm:ss");
                DateAndTime dateAndTime = new DateAndTime(df.format(new Date(milliseconds)).concat("Z"));
                metricPointBuilder.setTimestamp(dateAndTime);

                // Translate Prometheus metric value
                metricPointBuilder.setValue(value);
                // Building PAGODA MetricPoint object with single Prometheus metric information
                MetricPointSingle metricPoint = metricPointBuilder.build();
                metricPointsBuilder.setMetricPointsChoice(metricPoint);
            }else{
                if(metricPointsChoice instanceof org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.rev211118.metric.point.set.metric.points.metric.points.choice.MetricPointList){
                    org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.rev211118.metric.point.set.metric.points.metric.points.choice.MetricPointList prom_metricPointList = (org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.rev211118.metric.point.set.metric.points.metric.points.choice.MetricPointList) metricPointsChoice;
                    // Instantiate PAGODA MetricPointListBuilder object to record single Prometheus metric data
                    MetricPointListBuilder metricPointListBuilder = new MetricPointListBuilder();
                    MetricPointBuilder metricPointBuilder = new MetricPointBuilder();
                    Map<MetricPointKey,MetricPoint> metricPoint_map = new HashMap<MetricPointKey,MetricPoint>();
                    for(Map.Entry<org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.rev211118.metric.point.set.metric.points.metric.points.choice.metric.point.list.MetricPointKey, org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.rev211118.metric.point.set.metric.points.metric.points.choice.metric.point.list.MetricPoint> prom_metricPoint: prom_metricPointList.getMetricPoint().entrySet()){
                        java.math.BigDecimal timestamp = prom_metricPoint.getValue().getTimestamp();
                        //Long nano2milli = TimeUnit.MILLISECONDS.toMillis(Long.parseLong(timestamp.toString()));
                        Long milliseconds = timestamp.multiply(new BigDecimal(1000)).longValue();
                        DateFormat df = new SimpleDateFormat("Y-MM-dd'T'HH:mm:ss");
                        DateAndTime dateAndTime = new DateAndTime(df.format(new Date(milliseconds)).concat("Z"));
                        metricPointBuilder.setTimestamp(dateAndTime);
                        java.math.BigDecimal value = prom_metricPoint.getValue().getValue();
                        metricPointBuilder.setValue(value);
                        MetricPoint metricPoint = metricPointBuilder.build();
                        metricPoint_map.put(metricPoint.key(), metricPoint);
                    }
                    metricPointListBuilder.setMetricPoint(metricPoint_map);
                    // Building PAGODA MetricPointList object with a list of Prometheus metrics information
                    MetricPointList pagoda_metricPointList = metricPointListBuilder.build();
                    metricPointsBuilder.setMetricPointsChoice(pagoda_metricPointList);
                }
            }

            MetricPoints metricPoints = metricPointsBuilder.build();

            // Get Prometheus metric name
            String metric_name = prom_metric.getValue().getName();

            // Translate Prometheus metric labels, instantiating builder objects
            LabelBuilder pagoda_labelBuilder = new LabelBuilder();
            ArrayList<Label> pagoda_label_list = new ArrayList<Label>();
            LabelsBuilder pagoda_labels_builder = new LabelsBuilder();

            // Get Prometheus metric labels
            org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.rev211118.label.set.Labels prom_labels = prom_metric.getValue().getLabels();
            
            // Map (dictionary) with Prometheus metric name and labels to calculate the Hash code required for label-set-id YANG node in PAGODA YANG model
            Map<String, String> dictionary_prom_labels = new HashMap<String, String>();
            // Adding Prometheus metric name in the dictionary for calculating the Hash code
            dictionary_prom_labels.put("__name__", metric_name);
            
            // Mapping/translate Prometheus labels to PAGODA labels
            for (Map.Entry<LabelKey, org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.rev211118.label.set.labels.Label> entry: prom_labels.getLabel().entrySet()){
                pagoda_labelBuilder.setName(entry.getValue().getName());
                pagoda_labelBuilder.setValue(entry.getValue().getValue());
                Label pagoda_label = pagoda_labelBuilder.build();
                pagoda_label_list.add(pagoda_label);
                // Adding Prometheus labels in the dictionary for calculating the Hash code 
                dictionary_prom_labels.put(entry.getValue().getName(), entry.getValue().getValue());
            }

            // Building PAGODA Labels
            pagoda_labels_builder.setLabel(pagoda_label_list);
            Labels pagoda_labels = pagoda_labels_builder.build();

            // Instantiate PAGODA MetricBuilder object and building the regarding Metric with the corresponding metric point, labels and label-set-id
            org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.metrics.MetricBuilder pagoda_metricBuilder = new  org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.metrics.MetricBuilder();
            pagoda_metricBuilder.setName(metric_name);
            pagoda_metricBuilder.setMetricPoints(metricPoints);
            pagoda_metricBuilder.setLabels(pagoda_labels);
            pagoda_metricBuilder.setLabelSetId(Integer.toString(dictionary_prom_labels.hashCode()));
            org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.metrics.Metric pagoda_metric = pagoda_metricBuilder.build();
            pagoda_metric_list.add(pagoda_metric);
        }

        // Building the regarding PAGODA Metrics object with the corresponding Prometheus metric list
        pagoda_metricsBuilder.setMetric(pagoda_metric_list);
        org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.Metrics pagoda_metrics = pagoda_metricsBuilder.build();

        InstanceIdentifier<org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.Metrics> pagoda_iid = InstanceIdentifier.create(org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.Metrics.class);
        Entry<YangInstanceIdentifier, NormalizedNode<?, ?>> normalized = codec.toNormalizedNode(pagoda_iid, pagoda_metrics);
        JsonObject driver_output = doConvert(schemaContext, schemaContext.getPath(), normalized.getValue());
                
        return driver_output.toString();    
    }
}
