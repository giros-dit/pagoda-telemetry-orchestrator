package org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805;
import javax.annotation.processing.Generated;
import org.opendaylight.yangtools.yang.binding.DataRoot;

/**
 * YANG module to represent metrics collected from Prometheus HTTP API.
 *
 * <p>
 * This class represents the following YANG schema fragment defined in module <b>prometheus-pagoda</b>
 * <pre>
 * module prometheus-pagoda {
 *   yang-version 1.1;
 *   namespace "http://data-aggregator.com/ns/prometheus-pagoda";
 *   prefix prom-pagoda;
 *   import ietf-yang-types {
 *     prefix yang;
 *   }
 *   revision 2022-08-05 {
 *   }
 *   revision 2021-11-18 {
 *   }
 *   grouping label-set {
 *     container labels {
 *       list label {
 *         key name;
 *         leaf name {
 *           type string;
 *         }
 *         leaf value {
 *           type string;
 *         }
 *       }
 *     }
 *   }
 *   grouping metric-point-set {
 *     container metric-points {
 *       choice metric-points-choice {
 *         case metric-point-single {
 *           leaf value {
 *             type decimal64 {
 *               fraction-digits 2;
 *             }
 *           }
 *           leaf timestamp {
 *             type yang:date-and-time;
 *           }
 *         }
 *         case metric-point-list {
 *           list metric-point {
 *             when not(../metric-point);
 *             key timestamp;
 *             min-elements 2;
 *             leaf value {
 *               type decimal64 {
 *                 fraction-digits 2;
 *               }
 *             }
 *             leaf timestamp {
 *               type yang:date-and-time;
 *             }
 *           }
 *         }
 *       }
 *     }
 *   }
 *   container metrics {
 *     list metric {
 *       key label-set-id;
 *       leaf label-set-id {
 *         type string;
 *       }
 *       leaf name {
 *         type string;
 *       }
 *       uses label-set;
 *       uses metric-point-set;
 *     }
 *   }
 * }
 * </pre>
 *
 */
@Generated("mdsal-binding-generator")
public interface PrometheusPagodaData
    extends
    DataRoot
{




    /**
     * Return metrics, or {@code null} if it is not present.
     *
     * <pre>
     *     <code>
     *         Enclosing container for the list of Prometheus metrics.
     *     </code>
     * </pre>
     *
     * @return {@code org.opendaylight.yang.gen.v1.http.data.aggregator.com.ns.prometheus.pagoda.rev220805.Metrics} metrics, or {@code null} if it is not present.
     *
     */
    Metrics getMetrics();

}

