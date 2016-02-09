package org.distributedsearch.node;

import javax.xml.bind.annotation.*;

@XmlRootElement(name="searchResult")
@XmlAccessorType(XmlAccessType.FIELD)
public class SearchResult {

	@XmlElement(name = "search")
	public Search search;
	
	@XmlElement(name = "searchNode")
	public String searchNode;
	
	@XmlElement(name = "resultItems")
	public ResultItem[] resultItems;
}