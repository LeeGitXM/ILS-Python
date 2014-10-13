/**
 *   (c) 2013  ILS Automation. All rights reserved.
 */
package com.ils.blt.test.gateway.tag;

import java.util.Enumeration;
import java.util.Hashtable;

import com.inductiveautomation.ignition.common.sqltags.model.types.TagEditingFlags;
import com.inductiveautomation.ignition.common.sqltags.model.types.TagType;
import com.inductiveautomation.ignition.common.util.LogUtil;
import com.inductiveautomation.ignition.common.util.LoggerEx;
import com.inductiveautomation.ignition.gateway.model.GatewayContext;
import com.inductiveautomation.ignition.gateway.sqltags.simple.SimpleTagProvider;

/**
 *  The Singleton instance is a container for currently defined SimpleTagProvider
 *  instances. The hashtable holding instances of the provider is keyed by
 *  the provider name.
 *  
 *  A SimpleTagProvider is NOT a TagProvider, but its methods for creating
 *  and updating tags are much easier. Consequently, we will look in this
 *  registry first when looking for a provider.
 */
public class ProviderRegistry   {
	private static final String TAG = "ProviderRepository: ";
	private static ProviderRegistry instance = null;
	private final LoggerEx log;
	private final Hashtable<String,SimpleTagProvider> providerMap;
	
	/**
	 * Static method to create and/or fetch the single instance.
	 */
	public static ProviderRegistry getInstance() {
		if( instance==null) {
			synchronized(ProviderRegistry.class) {
				instance = new ProviderRegistry();
			}
		}
		return instance;
	}
	/**
	 * Constructor is private per the Singleton pattern.
	 */
	private ProviderRegistry() {;
		log = LogUtil.getLogger(getClass().getPackage().getName());
		providerMap = new Hashtable<String,SimpleTagProvider>() ;
	}


	public void createProvider(GatewayContext context,String providerName ) {
		log.info(TAG+"createProvider: "+providerName);
		SimpleTagProvider provider = providerMap.get(providerName);
		if( provider !=null ) return;  // Already exists, do nothing
		
		provider = new SimpleTagProvider(providerName);
		provider.configureTagType(TagType.Custom, TagEditingFlags.STANDARD_STATUS.or(TagEditingFlags.SUPPORTS_VALUE_EDIT), null);
		try {
			provider.startup(context);
			providerMap.put(providerName, provider);
		}
		catch(Exception ex) {
			log.error(TAG+"createProvider: Failed with exception ("+ex.getMessage()+")");
		}
	}
	
	/**
	 * 
	 * @param name
	 * @return may be null, if the provider has not previously been defined.
	 */
	public SimpleTagProvider getProvider(String name) {
		SimpleTagProvider provider = providerMap.get(name);
		return provider;
	}

	/**
	 * Remove the named provider. Removing a provider, removes all the tags
	 * that it provides.
	 * 
	 * @param name
	 */
	public void removeProvider(String name) {
		SimpleTagProvider provider = providerMap.get(name);
		if( provider!=null ) {
			provider.shutdown();
			providerMap.remove(name);
		}
 	}
	
	/**
	 * This method is meant to be called by the GatewayHook on module
	 * shutdown. It shuts down all the providers and clears the list.
	 */
	public void shutdown() {
		Enumeration<SimpleTagProvider> providerWalker = providerMap.elements();
		SimpleTagProvider provider = null;
		while( providerWalker.hasMoreElements() ) {
			provider = providerWalker.nextElement();
			provider.shutdown();
		}
		providerMap.clear();
	}
	
	
	
}
