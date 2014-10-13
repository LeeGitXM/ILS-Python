/**
 *   (c) 2013  ILS Automation. All rights reserved.
 */
package com.ils.blt.test.gateway.tag;

import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Date;
import java.util.List;

import com.inductiveautomation.ignition.common.model.values.BasicQualifiedValue;
import com.inductiveautomation.ignition.common.model.values.BasicQuality;
import com.inductiveautomation.ignition.common.model.values.QualifiedValue;
import com.inductiveautomation.ignition.common.model.values.Quality;
import com.inductiveautomation.ignition.common.sqltags.BasicTagValue;
import com.inductiveautomation.ignition.common.sqltags.TagDefinition;
import com.inductiveautomation.ignition.common.sqltags.model.Tag;
import com.inductiveautomation.ignition.common.sqltags.model.TagManagerBase;
import com.inductiveautomation.ignition.common.sqltags.model.TagNode;
import com.inductiveautomation.ignition.common.sqltags.model.TagPath;
import com.inductiveautomation.ignition.common.sqltags.model.TagProp;
import com.inductiveautomation.ignition.common.sqltags.model.types.AccessRightsType;
import com.inductiveautomation.ignition.common.sqltags.model.types.DataQuality;
import com.inductiveautomation.ignition.common.sqltags.model.types.DataType;
import com.inductiveautomation.ignition.common.sqltags.model.types.TagType;
import com.inductiveautomation.ignition.common.sqltags.model.types.TagValue;
import com.inductiveautomation.ignition.common.sqltags.parser.TagPathParser;
import com.inductiveautomation.ignition.common.sqltags.tags.TagDiff;
import com.inductiveautomation.ignition.common.util.LogUtil;
import com.inductiveautomation.ignition.common.util.LoggerEx;
import com.inductiveautomation.ignition.gateway.model.GatewayContext;
import com.inductiveautomation.ignition.gateway.sqltags.TagProvider;
import com.inductiveautomation.ignition.gateway.sqltags.simple.SimpleTagProvider;
import com.inductiveautomation.ignition.gateway.sqltags.simple.WriteHandler;

/**
 *  Provide for the creation, deleting and updating of SQLTags.
 */
public class TagHandler  {
	private static final String TAG = "TagHandler";
	private static final String TIMESTAMP_FORMAT = "yyyy.MM.dd HH:mm:ss.SSS";        // Format for writing timestamp
	private final LoggerEx log;
	private final GatewayContext context;
	private final SimpleDateFormat dateFormat;
	
	/**
	 * Constructor.
	 */
	public TagHandler(GatewayContext ctxt) {
		this.context = ctxt;
		this.dateFormat = new SimpleDateFormat(TIMESTAMP_FORMAT);
		log = LogUtil.getLogger(getClass().getPackage().getName());
	}
	
	/**
	 * An Expression is just a tag with an expression attribute. This method creates a tag that is an
	 * expression, but the expression is empty. Edit the tag to set an expression.
	 * The TagPath attribute "source" actually refers to the provider name. A full tag path includes
	 * the provider in brackets, a partial path does not. 
	 * @param providerName
	 * @param tagPath
	 * @param type - data type
	 */
	public void createExpression(String providerName, String tagPath, String type, String expr) {
		log.trace(TAG+": createExpression ["+providerName+"]"+tagPath+"("+type+")");
		TagPath tp = null;
		try {
			tp = TagPathParser.parse(providerName,tagPath);
		}
		catch(IOException ioe) {
			log.warn(TAG+String.format("createExpression: Exception parsing tag %s (%s)",tagPath,ioe.getLocalizedMessage()));
			return;
		}
		// In the case of Unit-tests we use the simple tag provider.
		DataType dataType = dataTypeFromString(type);
		TagProvider provider = context.getTagManager().getTagProvider(providerName);
		if( provider != null ) {
			try {
				TagDefinition tag = new TagDefinition(tp.getItemName(), TagType.Custom);
				TagValue tv = new BasicTagValue(expr);
				tag.setAttribute(TagProp.Expression,tv );
				tag.setDataType(dataType);
				tag.setEnabled(true);
				tag.setAccessRights(AccessRightsType.Custom); 
				context.getTagManager().addTags(tp.getParentPath(), Arrays.asList(new TagNode[] { tag }), TagManagerBase.CollisionPolicy.Abort);
			}
			catch(Exception ex) {
				log.warnf("%s: createTag: Exception creating tag %s (%s)",TAG,tagPath,ex.getLocalizedMessage());
			}
		}
		else {
				log.warn(TAG+"createTag: Provider "+providerName+" does not exist");
		}
	}


	/**
	 * The TagPath attribute "source" actually refers to the provider name. A full tag path includes
	 * the provider in brackets, a partial path does not. 
	 * @param providerName
	 * @param tagPath
	 * @param type
	 */
	public void createTag(String providerName, String tagPath, String type) {
		log.tracef("%s: createTag [%s] %s (%s)",TAG,providerName,tagPath,type);
		TagPath tp = null;
		try {
			tp = TagPathParser.parse(providerName,tagPath);
		}
		catch(IOException ioe) {
			log.warnf("%s: createTag: Exception parsing tag %s (%s)",TAG,tagPath,ioe.getLocalizedMessage());
			return;
		}
		// NOTE: The experience here is that if we use the simple data provider, then the tags 
		//       show up in the designer SQLTagsBrowser. This is not the case when defining directly
		//       through the tag manager. Here the calls appear to succeed, but the tags do not show up.
		// In the case of Unit-tests we use the simple tag provider.
		DataType dataType = dataTypeFromString(type);
		SimpleTagProvider simpleProvider = ProviderRegistry.getInstance().getProvider(providerName);
		TagProvider provider = context.getTagManager().getTagProvider(providerName);
		if( simpleProvider!=null) {
			simpleProvider.configureTag(tp, dataType, TagType.Custom);
			WriteHandler handler = new BasicTagWriter(simpleProvider);
			simpleProvider.registerWriteHandler(tp, handler);
		}
		else if( provider != null ) {
			try {
				TagDefinition tag = new TagDefinition(tp.getItemName(), TagType.Custom);
				tag.setDataType(dataType);
				tag.setEnabled(true);
				tag.setAccessRights(AccessRightsType.Custom);    // Or Read_write?
				context.getTagManager().addTags(tp.getParentPath(), Arrays.asList(new TagNode[] { tag }), TagManagerBase.CollisionPolicy.Abort);
			}
			catch(Exception ex) {
				log.warnf("%s: createTag: Exception creating tag %s (%s)",TAG,tagPath,ex.getLocalizedMessage());
			}
		}
		else {
				log.warn(TAG+"createTag: Provider "+providerName+" does not exist");
		}
	}


	public void deleteTag(String providerName, String tagPath) {
		log.debug(TAG+": DeleteTag ["+providerName+"]"+tagPath);
		TagPath tp = null;
		try {
			tp = TagPathParser.parse(providerName,tagPath);
		}
		catch(IOException ioe) {
			log.warnf("%s: deleteTag: Exception parsing tag %s (%s)",TAG,tagPath,ioe.getLocalizedMessage());
			return;
		}
		
		SimpleTagProvider simpleProvider = ProviderRegistry.getInstance().getProvider(providerName);
		if( simpleProvider!=null) {
			simpleProvider.removeTag(tp);
		}
		else {
			TagProvider provider = context.getTagManager().getTagProvider(providerName);
			if( provider != null  ) {
				List<TagPath> tags = new ArrayList<TagPath>();
				tags.add(tp);
				try {
					context.getTagManager().removeTags(tags);
				}
				catch(Exception ex) {
					log.warnf("%s: deleteTag: Exception deleting tag %s (%s)",TAG,tagPath,ex.getLocalizedMessage());
				}
			}
			else {
				log.warn(TAG+"deleteTag: Provider "+providerName+" does not exist");
			}
		}
	}

	/**
	 * Update a tag expression. If the tag was created by a simple provider, then we use that interface.
	 * Otherwise use the standard TagProvider constructs. If the value is "BAD", then conclude that 
	 * the quality is bad.
	 * 
	 * @param providerName
	 * @param tagPath
	 * @param expr, the new expression.
	 */
	public synchronized void updateExpression(String providerName, String tagPath, String expr) {
		log.debugf("%s: updateExpression %s to %s",TAG,tagPath,expr);
		if(providerName==null || tagPath==null) return;

		TagPath tp = null;
		Tag tag    = null; 
		TagProvider provider = context.getTagManager().getTagProvider(providerName);
		if( provider != null  ) {
			try {
				tp = TagPathParser.parse(providerName,tagPath);
				tag = provider.getTag(tp);
			}
			catch(IOException ioe) {
				log.warnf(TAG+"%s: updateExpression: Exception parsing tag name (%s)",TAG,ioe.getLocalizedMessage());
				return;
			}
		}
		else {
			log.warn(TAG+"updateExpression: Provider "+providerName+" does not exist");
			return;
		}

		// The SimpleTagProvider, does not seem to provide a mechanism to alter the expression,
		// so we simply delete and create another.
		SimpleTagProvider simpleProvider = ProviderRegistry.getInstance().getProvider(providerName);
		if( simpleProvider!=null) {
			deleteTag(providerName,tagPath);
			createExpression(providerName,tagPath,tag.getDataType().toString(),expr);
		}
		else if( provider!=null ) { 
			List<TagPath> tags = new ArrayList<TagPath>();
			tags.add(tp);
			Quality q = new BasicQuality("UnitTest",Quality.Level.Good);
			QualifiedValue qv = new BasicQualifiedValue( expr,q);
			TagValue tv = new BasicTagValue(qv);
			TagDiff diff = new TagDiff();
			diff.setAttribute(TagProp.Expression,tv);
			try {
				context.getTagManager().editTags(tags, diff);
			}
			catch(Exception ex) {
				log.warnf("%s: updateTag: Exception updating %s (%s)",TAG,tp.toStringFull(),ex.getLocalizedMessage());
			}
		}
	}

	/**
	 * Update a tag value. If the tag was created by a simple provider, then we use that interface.
	 * Otherwise use the standard TagProvider constructs. If the value is "BAD", then conclude that 
	 * the quality is bad. Do not update the value.
	 * 
	 * @param providerName
	 * @param tagPath
	 * @param value
	 * @param timestamp - the new value will be assigned this timestamp.
	 */
	public synchronized void updateTag(String providerName, String tagPath, String value,Date timestamp) {
		log.debugf("%s: updateTag %s to %s at %s",TAG,tagPath,value,dateFormat.format(timestamp));
		if(providerName==null || tagPath==null) return;

		TagPath tp = null;
		Tag tag    = null;
		Object val = value;
		if( timestamp==null ) timestamp = new Date(); 
		TagProvider provider = context.getTagManager().getTagProvider(providerName);
		if( provider != null  ) {
			try {
				tp = TagPathParser.parse(providerName,tagPath);
				tag = provider.getTag(tp);
				if( tag!=null ) {
					DataType dtype = tag.getDataType();
					if( value.equalsIgnoreCase("BAD") ) {
						;  // Do nothing, leave the value as-is
					}
					else if( dtype==DataType.Float4 ||
							dtype==DataType.Float8 )     val = Double.parseDouble(value);
					else if( dtype==DataType.Int1 ||
							dtype==DataType.Int2 ||
							dtype==DataType.Int4 ||
							dtype==DataType.Int8   )     val = Integer.parseInt(value);
					else val = val.toString();
				}
				else {
					log.warn(TAG+": updateTag: Tag "+tagPath.toString()+", not found");
					return;
				}
			}
			catch(IOException ioe) {
				log.warn(TAG+": updateTag: Exception parsing tag name ("+ioe.getLocalizedMessage()+")");
				return;
			}
			catch(NumberFormatException nfe) {
				log.warn(TAG+"updateTag: Exception setting tag value ("+nfe.getLocalizedMessage()+")");
				return;
			}
		}
		else {
			log.warn(TAG+": updateTag: Provider "+providerName+" does not exist");
			return;
		}

		// It appears as if the SimpleTagProvider has a timing issue. 
		// We feed it rapid changes, and it reports multiple updates to the subscriber
		// for the first tag in the bunch and ignores the rest.
		SimpleTagProvider simpleProvider = ProviderRegistry.getInstance().getProvider(providerName);
		if( simpleProvider!=null) {		
			if( value.equalsIgnoreCase("BAD")) {
				val = tag.getValue().getValue();
				QualifiedValue qv = new BasicQualifiedValue( val,DataQuality.OPC_BAD_DATA,timestamp);
				simpleProvider.updateValue(tp, qv);
			}
			else {
				QualifiedValue qv = new BasicQualifiedValue( val,DataQuality.GOOD_DATA,timestamp);
				simpleProvider.updateValue(tp, qv);
			}
		}
		else if( provider!=null ) { 
			List<TagPath> tags = new ArrayList<TagPath>();
			tags.add(tp);
			Quality q = new BasicQuality("UnitTest",Quality.Level.Good);
			QualifiedValue qv = new BasicQualifiedValue( val,q,timestamp);
			TagValue tv = new BasicTagValue(qv);
			TagDiff diff = new TagDiff();
			diff.setAttribute(TagProp.Value,tv);
			try {
				context.getTagManager().editTags(tags, diff);
			}
			catch(Exception ex) {
				log.warnf("%s: updateTag: Exception updating %s (%s)",TAG,tp.toStringFull(),ex.getLocalizedMessage());
			}
		}
	}

	/**
	 * Convert a string data type into a data type object
	 */
	private DataType dataTypeFromString( String type ) {
		DataType result = DataType.valueOf(type);
		return result;
	}
}
